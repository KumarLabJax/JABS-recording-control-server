
from hashlib import sha512
from uuid import uuid1
import datetime

from sqlalchemy import Column, String, Integer, ForeignKey, TIMESTAMP
from sqlalchemy.exc import SQLAlchemyError
from sqlalchemy.orm import relationship

from . import BASE, SESSION, JaxMBADatabaseException, PasswordFormatException
from . import User
from src.utils.exceptions import CredentialError

MIN_PASSWORD_LEN = 8
RESET_TOKEN_VALID_DAYS = 1


class SimpleAuth(BASE):
    __tablename__ = 'simple_auth'

    uid = Column(Integer, ForeignKey(User.id), primary_key=True)
    salt = Column(String, nullable=False)
    password_hash = Column(String, nullable=False)
    password_reset_token = Column(String, nullable=True)
    password_reset_token_expiration = Column(TIMESTAMP(timezone=True), nullable=True)

    user = relationship('User')

    @classmethod
    def create_admin(cls, email_address, password):
        cls.create_user(email_address, password, True)

    @classmethod
    def create_user(cls, email_address, password=None, admin=False):
        email_address = email_address.strip()
        email_lower = email_address.lower()
        password_reset_token = None
        password_reset_token_expiration = None

        salt = str(uuid1())

        # if a password isn't specified, generate a random one and set the
        # password_reset_token
        if password is None:
            password = str(uuid1())
            password_reset_token = str(uuid1())
            password_reset_token_expiration = \
                datetime.datetime.utcnow() + datetime.timedelta(days=1)

        password_hash = cls.hash_str(password + salt)

        user_auth = SimpleAuth(
            password_hash=password_hash,
            salt=salt,
            password_reset_token=password_reset_token,
            password_reset_token_expiration=password_reset_token_expiration
        )
        user_auth.user = User(
            email_address=email_address,
            email_address_lowercase=email_lower,
            admin=admin
        )

        SESSION.add(user_auth)
        try:
            SESSION.commit()
        except SQLAlchemyError:
            SESSION.rollback()
            raise JaxMBADatabaseException("unable to add new user")

        return user_auth.user

    @classmethod
    def get_user_auth(cls, uid):
        return SESSION.query(cls).get(uid)

    @staticmethod
    def authenticate(email_address, password):
        """
        authenticates a user with a given email address and password
        :param email_address: user email address
        :param password: user password
        :return: user, None if user can't be authenticated
        """
        user = SESSION.query(User).filter(User.email_address_lowercase == email_address.lower()).one_or_none()

        if user:
            auth_data = SESSION.query(SimpleAuth).filter(SimpleAuth.uid == user.id).one_or_none()
            if auth_data and auth_data.check_password(password):
                return user

        # user not found or password does not match
        raise CredentialError

    @staticmethod
    def hash_str(s):
        return sha512(bytes(s, 'utf-8')).hexdigest()

    def update_password(self, new_password):
        if len(new_password) < MIN_PASSWORD_LEN:
            raise PasswordFormatException("password must be at least 8 characters")
        self.password_hash = self.hash_str(new_password + self.salt)
        self.password_reset_token_expiration = None
        self.password_reset_token = None
        try:
            SESSION.commit()
        except SQLAlchemyError:
            SESSION.rollback()
            raise JaxMBADatabaseException("unable to update password")

    def check_password(self, password):
        return self.hash_str(password + self.salt) == self.password_hash

    def check_reset_token(self, token):
        return self.password_reset_token == token

    def token_is_expired(self):
        now = datetime.datetime.utcnow()
        return self.password_reset_token_expiration < now

    def generate_reset_token(self):
        try:
            with SESSION.begin_nested():
                self.password_reset_token = str(uuid1())
                self.password_reset_token_expiration = \
                    datetime.datetime.utcnow() + \
                    datetime.timedelta(days=RESET_TOKEN_VALID_DAYS)
        except SQLAlchemyError:
            raise JaxMBADatabaseException(
                "unable to create password reset token")

    def clear_reset_token(self):
        try:
            with SESSION.begin_nested():
                self.password_reset_token = None
                self.password_reset_token_expiration = None
        except SQLAlchemyError:
            raise JaxMBADatabaseException(
                "unable to clear password reset token")
