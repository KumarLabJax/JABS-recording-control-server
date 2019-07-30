"""
Interact with ldap
"""

import ldap
import ldap.filter
import flask


__author__ = "Glen Beane"
__contact__ = "glen.beane@jax.org"
__status__ = "Production"
__date__ = "03/22/2019"


# Disable "Modeule 'ldap' has no <> member
#   ldap indeed has those member, pylint just doesn't know
# pylint: disable=E1101

# allow self-signed certificates
# (needed since ldaps.jax.org uses one signed by JAX)
ldap.set_option(ldap.OPT_X_TLS_REQUIRE_CERT, ldap.OPT_X_TLS_ALLOW)


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


def __get_ldap_config():
    return flask.current_app.config['LDAP']


def __ldap_response_to_dict(response):
    """
    convert a response from search_s into a dictionary assuming we've already
    made sure that our search returned an expected result
    :param response:
    :return:
    """
    return {
        'first_name': response[0][1]['givenName'][0].decode("utf-8"),
        'last_name': response[0][1]['sn'][0].decode("utf-8"),
        'email': response[0][1]['mail'][0].decode("utf-8"),
        'username': response[0][1]['sAMAccountName'][0].decode("utf-8")
    }


def __search_ldap(search_string):
    """
    search LDAP given a search string
    :param search_string:
    :return: results from calling search_s with the given search string
    """
    config = __get_ldap_config()
    con = __connect()
    try:
        return con.search_s(config['BASE'], ldap.SCOPE_SUBTREE, search_string,
                            ['givenName', 'sn', 'mail', 'sAMAccountName'])
    except ldap.TIMEOUT:
        raise Timeout("LDAP Search Timeout")


def __connect():
    """
    connect and bind to ldap server
    :return: bound connection
    """
    config = __get_ldap_config()
    con = ldap.initialize(config['HOST'], bytes_mode=False)
    con.set_option(ldap.OPT_REFERRALS, 0)
    con.simple_bind_s('{}@{}'.format(config['USER'],
                                     config['USER_DOMAIN']),
                      config['PW'])
    return con


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
    con = ldap.initialize(config['HOST'], bytes_mode=False)
    con.set_option(ldap.OPT_REFERRALS, 0)

    # first try to authenticate the user
    try:
        con.simple_bind_s('{}@{}'.format(username, config['USER_DOMAIN']), password)
    except ldap.INVALID_CREDENTIALS:
        raise InvalidCredentials("Unable to authenticate username/password")

    try:
        # user is authenticated, get their information
        results = con.search_s(config['BASE'], ldap.SCOPE_SUBTREE,
                               "sAMAccountName={}".format(username),
                               ['givenName', 'sn', 'mail', 'sAMAccountName'])
    except ldap.TIMEOUT:
        raise Timeout("LDAP Search Timeout")

    return __ldap_response_to_dict(results)


def lookup_user_by_email(email):
    """
    lookup a user by email address
    :param email: jax email address
    :return: dictionary formatted by __ldap_response_to_dict()
    """
    results = __search_ldap("mail={}".format(email))

    if len(results) != 2:
        raise UserNotFound("user not found for email {}".format(email))

    return __ldap_response_to_dict(results)


def lookup_by_username(username):
    """
    lookup a user by username
    :param username: jax username
    :return: dictionary formatted by __ldap_response_to_dict()
    """
    results = __search_ldap("sAMAccountName={}".format(username))

    if len(results) != 2:
        raise UserNotFound("username {} not found".format(username))

    return __ldap_response_to_dict(results)


def get_user_groups(username):
    """
    get a list of groups a given user belongs to
    :param username: jax username
    :return: list of groups (strings)
    """
    config = __get_ldap_config()
    con = __connect()

    try:
        results = con.search_s(config['BASE'], ldap.SCOPE_SUBTREE,
                               "sAMAccountName={}".format(username),
                               ['memberOf'])

    except ldap.TIMEOUT:
        raise Timeout("LDAP Search Timeout")

    if len(results) != 2:
        raise UserNotFound("user not found ({})".format(username))

    groups = results[0][1]['memberOf']
    return [g.decode('utf-8').split(',')[0].replace('CN=', '') for g in groups]
