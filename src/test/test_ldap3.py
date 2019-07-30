"""
Tests related to LDAP connection and interactions
TO make these tests run and pass, make sure the config file with the following
LDAP info is in the test folder. Also make sure that the LDAP mock server files
(3 JSONs) are in /src/app/service/auth/ and are named after the file names in the config below.
[LDAP]
password = pa55word
user = testuser
host = ldaps://ldaps.jax.org:636
base = DC=jax,DC=org
user_domain = jax.org
search_filter = (&(sAMAccountName={})(memberOf=CN={},OU=Unix,OU=Groups,DC=jax,DC=org))
search_timeout = 10
strategy = MOCK_SYNC
mock_entries = mock_ldap_entries.json
mock_info = mock_ldap_info.json
mock_schema = mock_ldap_schema.json
"""
import unittest

from src.test import BaseTestCase
from src.app.service.auth.jax_ldap3 import connect, lookup_by_username, lookup_user_by_email,\
    authenticate_user, get_user_groups, UserNotFound


class LDAPTest(BaseTestCase):
    """
    Test the LDAP connection to the mock LDAP server
    """
    __config_name__ = 'test'

    def test_ldap_connect(self):
        """ Test the default connection """
        connection = connect()
        self.assertTrue(connection.entries)

    def test_authenticate_user(self):
        """ Test the authentication of a user """
        results = authenticate_user('testuser', 'pa55word')
        self.assertEqual(results['first_name'], 'Test')
        self.assertEqual(results['last_name'], 'User')
        self.assertEqual(results['email'], 'Test.User@jax.org')
        self.assertEqual(results['username'], 'testuser')
        self.assertEqual(len(results['groups']), 14)
        self.assertEqual(results['groups'][0], 'CN=CGRP-bhcape01,OU=Groups,DC=jax,DC=org')

    def test_lookup_by_email(self):
        """
        Test that an existing user is found with its email
        and that a non-existing user is not found
        """
        result = lookup_user_by_email('Test.User@jax.org')
        self.assertEqual(result['first_name'], 'Test')
        with self.assertRaises(UserNotFound):
            lookup_user_by_email('Idontexist@jax.org')

    def test_lookup_by_username(self):
        """
        Test that an existing user is found with its username
        and that a non-existing user is not found
        """
        result = lookup_by_username('testuser')
        self.assertEqual(result['last_name'], 'User')
        with self.assertRaises(UserNotFound):
            lookup_by_username('Idontexist')

    def test_get_user_groups(self):
        """ Test that the user groups of a user are correctly retrieved """
        groups = get_user_groups('testuser')
        self.assertEqual(groups[0], 'CGRP-bhcape01')
        self.assertEqual(groups[1], 'O365-Faculty-A1-Base')
        self.assertEqual(groups[2], 'BOX-JAX_All_Users')
        self.assertEqual(groups[3], 'GRP-BH_HDrive_Migration')
        self.assertEqual(groups[4], 'GRP-WebExUsers')


if __name__ == '__main__':
    unittest.main()
