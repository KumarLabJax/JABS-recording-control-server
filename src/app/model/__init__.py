"""
The root of our sqlalchemy code
"""
from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker, scoped_session
from sqlalchemy.ext.declarative import declarative_base
from flask_marshmallow import Marshmallow

from src.utils.exceptions import LTMSControlServiceException

MA = Marshmallow()

BASE = declarative_base()
SESSION_FACTORY = sessionmaker(autoflush=False,
                               autocommit=False)
SESSION = scoped_session(SESSION_FACTORY)
BASE.query = SESSION.query_property()


class LTMSDatabaseException(LTMSControlServiceException):
    """ Base exception class for exceptions defined in the model module """


class PasswordFormatException(LTMSControlServiceException):
    """password doesn't meet our requirements"""

# this needs to be imported after the BASE/SESSION and exceptions are setup
# pylint: disable=wrong-import-position
from .device_model import Device
from .recording_session_model import RecordingSession, DeviceRecordingStatus
from .user_model import User
from .simple_auth_model import SimpleAuth, MIN_PASSWORD_LEN
# pylint: enable=wrong-import-position


def init_db(app):
    """
    This method takes the current flask app and uses the
    'SQLALCHEMY_DATABASE_URI' config property to create
    an sqlalchemy engine and attach it to the session factory.

    :param app: The flask app returned from app_factory
    :return: sqlalchemy engine, just in case you want it
    """
    engine = create_engine(app.config['SQLALCHEMY_DATABASE_URI'])
    SESSION_FACTORY.configure(bind=engine)
    create_all(engine)
    return engine


def create_all(engine):
    """
    Create all the sqlalchemy tables
    :param engine:
    :return: None
    """
    BASE.metadata.create_all(engine, checkfirst=True)


def drop_all(engine):
    """
    Drop all of the sqlalchemy tables
    :param engine:
    :return: None
    """
    BASE.metadata.drop_all(engine)


def add_object(db_object):
    """
    wrapper for adding an object to the session
    :param db_object: ORM object
    :return: None
    """
    try:
        SESSION.add(db_object)
        SESSION.commit()
    except:
        SESSION.rollback()
        # TODO raise custom exception
        raise Exception("Error creating object")
