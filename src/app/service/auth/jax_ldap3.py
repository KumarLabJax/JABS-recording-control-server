"""
Interact with LDAP with ldap3
"""
import os
import flask
from ldap3 import Server, Connection, ALL_ATTRIBUTES,\
    SYNC, ASYNC, MOCK_SYNC, MOCK_ASYNC, RESTARTABLE, REUSABLE, LDIF
from ldap3.core.exceptions import LDAPTimeLimitExceededResult, LDAPException, LDAPBindError


from src import SRC_DIR


def __get_ldap_config():
    return flask.current_app.config['LDAP3']


STRATEGIES = {
    'SYNC': SYNC,
    'ASYNC': ASYNC,
    'MOCK_SYNC': MOCK_SYNC,
    'MOCK_ASYNC': MOCK_ASYNC,
    'RESTARTABLE': RESTARTABLE,
    'REUSABLE': REUSABLE,
    'LDIF': LDIF
}


def __get_strategy(strategy):
    """
    Return the ldap strategy matching the string provided
    :param strategy: string name of the ldap strategy to get
    :return: ldap3.strategy.base.BaseStrategy
    """
    return STRATEGIES.get(strategy, strategy)


# we define a few different exceptions so we can let the caller know why the
# user was not authenticated
class InvalidCredentials(Exception):
    """
    Credentials provided were not valid (username and/or password)
    Thrown instead of an ldap.INVALID_CREDENTIALS exception, so the rest of
    the app doesn't depend on the ldap module
    """


class NotInLoginGroup(Exception):
    """
    Thrown if the user is not a member of the required AD login group
    """


class Timeout(Exception):
    """
    searching ldap took too long
    """


class UserNotFound(Exception):
    """
    The specified user wasn't found
    """


class FileServerDoesNotExist(Exception):
    """
    The file server used for mocking does not exist
    """


def __ldap_response_to_dict(response):
    """
    convert a response from search_s into a dictionary assuming we've already
    made sure that our search returned an expected result
    :param response:
    :return:
    """
    return {
        'first_name': response[0]['givenName'].value,
        'last_name': response[0]['sn'].value,
        'email': response[0]['mail'].value,
        'username': response[0]['sAMAccountName'].value,
        'groups': response[0]['memberOf'].value
    }


def connect():
    """
    connect and bind to ldap server. Login and Password are needed in the configuration file.
    :return: bound connection
    """
    config = __get_ldap_config()
    username = config['USER']
    password = config['PW']
    server = __get_server(config)
    conn = __get_connection(server, username, password, config)
    return conn


def __search_ldap(search_string):
    """
    search LDAP given a search string
    :param search_string:
    :return: results from calling search_s with the given search string
    """
    config = __get_ldap_config()
    conn = connect()
    try:
        conn.search(config['BASE'], search_string, attributes=['givenName', 'sn', 'mail',
                                                               'sAMAccountName', 'memberOf'])
        return conn.entries
    except LDAPTimeLimitExceededResult:
        raise Timeout("LDAP Search Timeout")


def __get_server(config):
    strategy = config['STRATEGY']
    mock_info = config['MOCK_INFO']
    mock_schema = config['MOCK_SCHEMA']

    if strategy in ('MOCK_SYNC', 'MOCK_ASYNC'):
        info_fullpath = os.path.join(SRC_DIR, mock_info)
        schema_fullpath = os.path.join(SRC_DIR, mock_schema)
        if not os.path.isfile(info_fullpath):
            raise FileServerDoesNotExist(f'{mock_info} file could not be found')
        if not os.path.isfile(schema_fullpath):
            raise FileServerDoesNotExist(f'{mock_schema} file could not be found')
        server = Server.from_definition('MOCK_SERVER', info_fullpath, schema_fullpath)
    else:
        server = Server(config['HOST'], use_ssl=True)
    return server


def __get_connection(server, username, password, config):
    strategy = config['STRATEGY']
    if strategy in ('MOCK_SYNC', 'MOCK_ASYNC'):
        conn = Connection(server, client_strategy=strategy)
        # Populate the DIT of the fake server
        mock_entries = config['MOCK_ENTRIES']
        entries_fullpath = os.path.join(SRC_DIR, config['MOCK_ENTRIES'])
        if not os.path.isfile(entries_fullpath):
            raise FileServerDoesNotExist(f'{mock_entries} file could not be found')
        conn.strategy.entries_from_json(entries_fullpath)
        conn.bind()
        conn.search(config['BASE'], f'(&(sAMAccountName={username})(userPassword={password}))',
                    attributes=ALL_ATTRIBUTES)
        results = conn.entries
        if not results:     # If no results, it means it is a failed authentication attempt
            raise LDAPBindError
    else:
        conn = Connection(server, user=f"{username}@{config['USER_DOMAIN']}",
                          password=password, auto_bind=True, version=3,
                          authentication='SIMPLE', client_strategy=__get_strategy(strategy),
                          auto_referrals=True, check_names=True, read_only=False, lazy=False,
                          raise_exceptions=True)
        conn.search(config['BASE'], f"(sAMAccountName={username})", attributes=['*'])

    return conn


def authenticate_user(username, password):
    """
    authenticate a user against Jax's active directory
    :param username: username of user attempting to log in
    :param password: user's password
    :return:
    if successful, returns a dict containing the user's first and last names
    otherwise will raise an exception
    """
    config = __get_ldap_config()
    server = __get_server(config)

    # get connection
    try:
        conn = __get_connection(server, username, password, config)
    except LDAPBindError as exc:
        # If the LDAP bind failed for reasons such as authentication failure.
        raise InvalidCredentials("Unable to authenticate username/password:", exc)

    results = conn.entries
    return __ldap_response_to_dict(results)


def lookup_user_by_email(email):
    """
    lookup a user by email address
    :param email: jax email address
    :return: dictionary formatted by __ldap_response_to_dict()
    """
    results = __search_ldap(f'(mail={email})')
    if len(results) != 1:
        raise UserNotFound(f'user not found for email {email}')

    return __ldap_response_to_dict(results)


def lookup_by_username(username):
    """
    lookup a user by username
    :param username: jax username
    :return: dictionary formatted by __ldap_response_to_dict()
    """
    results = __search_ldap(f'(sAMAccountName={username})')
    if len(results) != 1:
        raise UserNotFound(f'username {username} not found')

    return __ldap_response_to_dict(results)


def get_user_groups(username):
    """
    get a list of groups a given user belongs to
    This method requires the local config files to have a valid username and password
    :param username: jax username
    :return: list of groups (strings)
    """
    config = __get_ldap_config()
    conn = connect()
    try:
        conn.search(config['BASE'], f'(sAMAccountName={username})', attributes=['memberOf'])
        results = conn.entries
    except LDAPTimeLimitExceededResult:
        raise Timeout("LDAP Search Timeout")
    except LDAPException:
        raise LDAPException
    if len(results) != 1:
        raise UserNotFound(f'user not found ({username})')

    groups = results[0]['memberOf'].value
    return [g.split(',')[0].replace('CN=', '') for g in groups]
