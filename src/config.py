"""
This module contains the configuration environments for the flask app
"""

# The next line disables specific pylint checking
# pylint: disable=W0223, R0903, W0511
# TODO: Remove previous lines when config file attributes and methods are fully implemented


import os
import configparser

from src.utils.config_tools import CONFIG_FILE_NAME, generate_secrets, create_empty_config

BASEDIR = os.path.abspath(os.path.dirname(__file__))

# Try to read the ltm_control_service.config file
_CFG = configparser.ConfigParser(allow_no_value=True)
_CFG_READ = _CFG.read(CONFIG_FILE_NAME)

# If nothing read, create it
if not _CFG_READ:
    create_empty_config()
    _CFG.read(CONFIG_FILE_NAME)

# Create secrets if not present
if not _CFG.get('MAIN', 'FLASK_SECRET') or not _CFG.get('MAIN', 'JWT_SECRET'):
    generate_secrets()
    _CFG.read(CONFIG_FILE_NAME)


class Config:
    """ This is the base config that's used by all other configs """

    # Defaults
    ENV = 'Default'
    DEBUG = False
    TESTING = False
    LOG_LEVEL = 'DEBUG'

    # Secrets
    SECRET_KEY = _CFG.get('MAIN', 'FLASK_SECRET')
    JWT_SECRET_KEY = _CFG.get('MAIN', 'JWT_SECRET')

    DOWN_DEVICE_THRESHOLD = int(_CFG.get('MAIN', 'DOWN_DEVICE_THRESHOLD'))

    ERROR_404_HELP = False
    RESTPLUS_MASK_SWAGGER = False

    # TODO: Fill in celery config
    # Celery
    CELERY_BROKER_URL = _CFG.get('CELERY', 'CELERY_BROKER_URL')
    CELERY_RESULT_BACKEND = _CFG.get('CELERY', 'CELERY_RESULT_BACKEND')
    CELERY_TRACK_STARTED = True

    # TODO: Fill in LDAP info
    # LDAP Config
    LDAP = {
        'PW': _CFG.get('LDAP', 'PASSWORD'),
        'USER': _CFG.get('LDAP', 'USER'),
        'HOST': _CFG.get('LDAP', 'HOST'),
        'BASE': _CFG.get('LDAP', 'BASE'),
        'USER_DOMAIN': _CFG.get('LDAP', 'USER_DOMAIN'),
        'SEARCH_FILTER': _CFG.get('LDAP', 'SEARCH_FILTER'),
        'SEARCH_TIMEOUT': _CFG.get('LDAP', 'SEARCH_TIMEOUT')
    }

    # TODO: Fill in LDAP info
    # LDAP3 Config
    LDAP3 = {
        'PW': _CFG.get('LDAP3', 'PASSWORD'),
        'USER': _CFG.get('LDAP3', 'USER'),
        'HOST': _CFG.get('LDAP3', 'HOST'),
        'BASE': _CFG.get('LDAP3', 'BASE'),
        'USER_DOMAIN': _CFG.get('LDAP3', 'USER_DOMAIN'),
        'SEARCH_FILTER': _CFG.get('LDAP3', 'SEARCH_FILTER'),
        'SEARCH_TIMEOUT': _CFG.get('LDAP3', 'SEARCH_TIMEOUT'),
        'STRATEGY': _CFG.get('LDAP3', 'STRATEGY'),
        'MOCK_ENTRIES': _CFG.get('LDAP3', 'MOCK_ENTRIES'),
        'MOCK_INFO': _CFG.get('LDAP3', 'MOCK_INFO'),
        'MOCK_SCHEMA': _CFG.get('LDAP3', 'MOCK_SCHEMA')
    }


class DevelopmentConfig(Config):
    """ Development Specific Config """
    ENV = 'Development'
    DEBUG = True
    LOG_LEVEL = 'DEBUG'
    SQLALCHEMY_DATABASE_URI = 'sqlite:///' + \
                              os.path.join(BASEDIR,
                                           'ltmcs.dev.sqlite.db')


class TestingConfig(Config):
    """ Testing Specific Config """
    ENV = 'Testing'
    DEBUG = True
    TESTING = True
    LOG_LEVEL = 'INFO'

    PRESERVE_CONTEXT_ON_EXCEPTION = False
    SQLALCHEMY_DATABASE_URI = 'sqlite:///' + \
                              os.path.join(BASEDIR,
                                           'ltmcs.test.sqlite.db')


class ProductionConfig(Config):
    """ Production Config. WARNING: BE CAREFUL """
    ENV = 'Production'
    DEBUG = False
    LOG_LEVEL = 'ERROR'

    SQLALCHEMY_DATABASE_URI = f"{_CFG.get('DATABASE', 'DIALECT')}://" \
         f"{_CFG.get('DATABASE', 'USERNAME')}:" \
         f"{_CFG.get('DATABASE', 'PASSWORD')}@" \
         f"{_CFG.get('DATABASE', 'HOST')}:" \
         f"{_CFG.get('DATABASE', 'PORT')}/" \
         f"{_CFG.get('DATABASE', 'DATABASE')}"


DEFAULT_CONFIG = DevelopmentConfig  # pylint: disable=C0103

CONFIG_BY_NAME = dict(
    dev=DevelopmentConfig,
    test=TestingConfig,
    prod=ProductionConfig
)

KEY = Config.SECRET_KEY
