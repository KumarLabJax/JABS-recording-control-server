""" Tests for the authentication endpoints """

import unittest
import requests
from faker import Faker
from flask import url_for

from src.test import BaseLiveServerTestCase


class AuthTest(BaseLiveServerTestCase):
    """ A class to test the auth endpoints """

    def test_auth_returns_access_and_refresh(self):
        """ The auth endpoint should give us a refresh and access token """
        fake = Faker()
        uri = self.get_server_url() + url_for('api.auth_user_login')
        data = {"username": fake.profile()['username'], "password": fake.password()} # pylint: disable=E1101
        response = requests.post(uri, json=data)
        self.assertTrue('refresh' in list(response.json().keys()))
        self.assertTrue('access' in list(response.json().keys()))

    def test_access_token_works(self):
        """ The access token should let us access a protected endpoint """
        fake = Faker()
        auth_uri = self.get_server_url() + url_for('api.auth_user_login')
        data = {"username": fake.profile()['username'], "password": fake.password()} # pylint: disable=E1101
        auth_response = requests.post(auth_uri, json=data)
        access_token = auth_response.json()['access']

        protected_uri = self.get_server_url() + url_for('api.hello_protected_hello_world')
        auth_header = {'Authorization': 'Bearer {}'.format(access_token)}
        protected_response = requests.get(protected_uri, headers=auth_header)
        self.assertEqual({"message": "Hello World!"}, protected_response.json())

    def test_refresh_token_works(self):
        """ The refresh token should get us a new access token """
        fake = Faker()
        auth_uri = self.get_server_url() + url_for('api.auth_user_login')
        data = {"username": fake.profile()['username'], "password": fake.password()} # pylint: disable=E1101
        auth_response = requests.post(auth_uri, json=data)
        refresh_token = auth_response.json()['refresh']

        refresh_uri = self.get_server_url() + url_for('api.auth_user_refresh')
        headers = {'Authorization': 'Bearer {}'.format(refresh_token)}
        refresh_response = requests.post(refresh_uri, headers=headers)
        self.assertTrue('access' in list(refresh_response.json().keys()))


if __name__ == '__main__':
    unittest.main()
