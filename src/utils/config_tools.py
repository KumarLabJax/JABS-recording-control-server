"""
Utilities to help manage the 'ltm_control_service.config' configuration file
"""
import os
import secrets
import configparser

from src.utils.logging import get_module_logger

CONFIG_FILE_NAME = 'ltm_control_service.config'

EXAMPLE_CELERY_URI = 'amqp://<USER>:<PASS>@<BROKER_URL>:<PORT>/<VHOST>'

LOGGER = get_module_logger()


def generate_secrets():
    """
    Write secret keys to fields in CONFIG_FILE_NAME
    :return:
    """
    config_dict = configparser.ConfigParser(allow_no_value=True)
    config_dict.read(CONFIG_FILE_NAME)

    if not config_dict.get('MAIN', 'FLASK_SECRET'):
        LOGGER.warning("Flask secret not found, GENERATING NEW SECRET")
        config_dict['MAIN']['FLASK_SECRET'] = secrets.token_hex(32)
    if not config_dict.get('MAIN', 'JWT_SECRET'):
        LOGGER.warning("JWT secret not found, GENERATING NEW SECRET")
        config_dict['MAIN']['JWT_SECRET'] = secrets.token_hex(32)

    with open(CONFIG_FILE_NAME, 'w') as configfile:
        config_dict.write(configfile)


def create_empty_config():
    """
    Creates an empty config file for the user to fill out
    :return:
    """
    # TODO: Include user prompts
    config_dict = configparser.ConfigParser(allow_no_value=True)
    config_dict['MAIN'] = {'FLASK_SECRET': '', 'JWT_SECRET': '', 'ADMIN_NAME': ''}
    config_dict['CELERY'] = {'CELERY_BROKER_URL': EXAMPLE_CELERY_URI,
                             'CELERY_RESULT_BACKEND': EXAMPLE_CELERY_URI}
    config_dict['LDAP'] = {
        'PASSWORD': '',
        'USER': '',
        'HOST': 'ldaps://ldaps.jax.org:636',
        'BASE': 'DC=jax,DC=org',
        'USER_DOMAIN': 'jax.org',
        'SEARCH_FILTER': '(&(sAMAccountName={})(memberOf=CN={},OU=Unix,OU=Groups,DC=jax,DC=org))',
        'SEARCH_TIMEOUT': 10
    }

    test_dir = 'test' + os.path.sep +'ldap' + os.path.sep
    config_dict['LDAP3'] = {
        'PASSWORD': 'pa55word', # this is a test password for the mock server
        'USER': 'testuser',     # this is a test username for the mock server
        'HOST': 'ldaps://ldaps.jax.org:636',
        'BASE': 'DC=jax,DC=org',
        'USER_DOMAIN': 'jax.org',
        'SEARCH_FILTER': '(&(sAMAccountName={})(memberOf=CN={},OU=Unix,OU=Groups,DC=jax,DC=org))',
        'SEARCH_TIMEOUT': 10,
        'STRATEGY': 'SYNC',    # set to MOCK strategy in order for the tests to pass
        'MOCK_ENTRIES': test_dir + 'mock_ldap_entries.json',
        'MOCK_INFO': test_dir + 'mock_ldap_info.json',
        'MOCK_SCHEMA': test_dir + 'mock_ldap_schema.json'
    }
    config_dict['DATABASE'] = {
        'DIALECT': 'postgres',
        'USERNAME': '',
        'PASSWORD': '',
        'HOST': 'localhost',
        'PORT': '5432',
        'DATABASE': ''
    }

    with open(CONFIG_FILE_NAME, 'w') as configfile:
        config_dict.write(configfile)


def get_config_file_attribute(key, section=None, check_all=False):
    """
    Get the value of an item in the .config static file. Useful for scripts, tasks, etc that
    do not have access to the config object in the flask app context, but which depend on
    manual configuration.
    :param key: The key to look for
    :param section: What section the key is in, defaults to 'MAIN'
    :param check_all: If true, will look in all sections for the key. Returns first found.
    :return: The value of the key in the config file
    """
    section = section or 'MAIN'
    config = configparser.ConfigParser(allow_no_value=True)
    config_was_read = config.read(CONFIG_FILE_NAME)

    if not config_was_read:
        raise FileNotFoundError(f"No file found at {CONFIG_FILE_NAME}")

    if section not in config.sections():
        raise KeyError(f"No section: {section}")

    value = config.get(section, key)

    if not value and check_all:
        for alt_section in config.sections():
            value = config.get(alt_section, key)
            if value:
                log_string = f"'{key}' not found in {section}, instead found in {alt_section}"
                LOGGER.warning(log_string)
                break

    if not value:
        raise KeyError(f"[{section}]: {key} does not have a value")

    return value
