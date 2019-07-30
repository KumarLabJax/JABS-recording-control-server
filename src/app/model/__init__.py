"""
The root of our sqlalchemy code
"""

from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker, scoped_session
from sqlalchemy.ext.declarative import declarative_base
from flask_marshmallow import Marshmallow

MA = Marshmallow()

BASE = declarative_base()
SESSION_FACTORY = sessionmaker(autoflush=False,
                               autocommit=False)
SESSION = scoped_session(SESSION_FACTORY)
BASE.query = SESSION.query_property()


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
    :return:
    """
    BASE.metadata.create_all(engine, checkfirst=True)


def drop_all(engine):
    """
    Drop all of the sqlalchemy tables
    :param engine:
    :return:
    """
    BASE.metadata.drop_all(engine)
