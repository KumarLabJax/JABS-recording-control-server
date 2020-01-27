from sqlalchemy import Column, String, Integer, Boolean
from sqlalchemy.exc import SQLAlchemyError

from . import BASE, SESSION, JaxMBADatabaseException


class User(BASE):
    """ model representing a user """
    __tablename__ = 'user'

    id = Column(Integer, primary_key=True, autoincrement=True)
    email_address = Column(String, nullable=False, unique=True)
    email_address_lowercase = Column(String, nullable=False, index=True, unique=True)
    admin = Column(Boolean, nullable=False, default=False)

    @classmethod
    def lookup(cls, email_address):
        """
        looks up a user by email address
        :param email_address: email address to lookup
        :return: user, None if user not found
        """
        return SESSION.query(cls).filter(
            cls.email_address_lowercase == email_address.lower()).one_or_none()

    @staticmethod
    def delete(user):
        SESSION.remove(user)
        try:
            SESSION.commit()
        except SQLAlchemyError:
            SESSION.rollback()
            raise JaxMBADatabaseException("unable to remove user from database")

    @classmethod
    def get(cls, uid):
        return SESSION.query(cls).get(uid)
