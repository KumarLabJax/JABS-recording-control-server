
from hashlib import sha512
import datetime
import pytz
import secrets

from sqlalchemy import Column, String, Integer, ForeignKey, TIMESTAMP
from sqlalchemy.exc import SQLAlchemyError
from sqlalchemy.orm import relationship

from . import BASE, SESSION, JaxMBADatabaseException, PasswordFormatException
from . import User
from src.utils.exceptions import CredentialError

MIN_PASSWORD_LEN = 8
RESET_TOKEN_VALID_DAYS = 1


class SimpleAuth(BASE):
    """
    this is a simple way to provide authentication for application users by
    associating the app users with a hashed password
    """
    __tablename__ = 'simple_auth'

    # user id, corresponds to a user in our user table
    uid = Column(Integer, ForeignKey(User.id), primary_key=True)

    # password salt, used to add a little randomness to the password before
    # hashing to make it more secure
    salt = Column(String, nullable=False)

    # hashed user password
    password_hash = Column(String, nullable=False)

    # token generated to allow a user to reset their password if they don't
    # know it (new user being invited) or have forgotten it
    password_reset_token = Column(String, nullable=True)

    # reset tokens are only valid for a limited time
    password_reset_token_expiration = Column(TIMESTAMP(timezone=False),
                                             nullable=True)

    user = relationship('User')

    @classmethod
    def create_user(cls, email_address, password=None, admin=False):
        """
        create a new user using the simple auth model
        :param email_address: user email address (must be unique)
        :param password: user password, randomly generated if not provided
        :param admin: if true grant admin privs to new user
        :return:
        """

        # for a user we store the email address as provided (preserve case)
        # as well as the email address converted to lower case
        email = email_address.strip()
        email_lower = email.lower()

        # new users default to not having a password reset token generated
        password_reset_token = None
        password_reset_token_expiration = None

        # password salt generated to add some randomness to hashed password
        salt = secrets.token_hex(15)

        # if a password isn't specified, generate a random one and set the
        # password_reset_token
        if password is None:
            password = secrets.token_hex(15)
            password_reset_token = secrets.token_urlsafe(24)
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
            email_address=email,
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
        """
        get authentication data for a given uid
        """
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
        """
        update user's password
        :param new_password: string containing new password
        """

        # enforce some rules for valid passwords
        if len(new_password) < MIN_PASSWORD_LEN:
            raise PasswordFormatException(
                f"password must be at least {MIN_PASSWORD_LEN} characters")
        self.password_hash = self.hash_str(new_password + self.salt)

        # setting a new password will invalidate a password reset token
        self.password_reset_token_expiration = None
        self.password_reset_token = None
        try:
            SESSION.commit()
        except SQLAlchemyError:
            SESSION.rollback()
            raise JaxMBADatabaseException("unable to update password")

    def check_password(self, password):
        """
        check to see if a given password matches the hashed password in the DB
        """
        return self.hash_str(password + self.salt) == self.password_hash

    def check_reset_token(self, token):
        """
        check to see if a given token matches the password reset token in the db
        """
        return self.password_reset_token == token

    def token_is_expired(self):
        """
        return true if the user's password reset token has expired
        """
        now = datetime.datetime.utcnow()
        if self.password_reset_token_expiration.tzinfo is not None:
            now = now.replace(tzinfo=pytz.UTC)
        return self.password_reset_token_expiration < now

    def generate_reset_token(self):
        """
        create a new password reset token for the user
        """
        self.password_reset_token = secrets.token_urlsafe(24)
        self.password_reset_token_expiration = \
            datetime.datetime.utcnow() + \
            datetime.timedelta(days=RESET_TOKEN_VALID_DAYS)
        try:
            SESSION.commit()
        except SQLAlchemyError:
            SESSION.rollback()
        except SQLAlchemyError:
            raise JaxMBADatabaseException(
                "unable to create password reset token")
