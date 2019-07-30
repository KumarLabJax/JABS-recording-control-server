"""
Tests the various configuration environments
"""

import unittest
from flask import current_app
from src.test import BaseTestCase


class TestDevelopmentConfig(BaseTestCase):
    """ Test the development config environment """
    __config_name__ = 'dev'

    def test_app_is_development(self):
        """ Check that the app is using the dev config """
        self.assertFalse(self.app.config['SECRET_KEY'] == 'my_precious')
        self.assertTrue(self.app.config['DEBUG'] is True)
        self.assertFalse(current_app is None)


class TestTestingConfig(BaseTestCase):
    """ Test the testing config environment """
    __config_name__ = 'test'

    def test_app_is_testing(self):
        """ Check that the app is using the testing config """
        self.assertFalse(self.app.config['SECRET_KEY'] == 'my_precious')
        self.assertTrue(self.app.config['DEBUG'])


class TestProductionConfig(BaseTestCase):
    """ Test the production config environment """
    __config_name__ = 'prod'

    def test_app_is_production(self):
        """ Test that the app is using the production config """
        self.assertTrue(self.app.config['DEBUG'] is False)


if __name__ == '__main__':
    unittest.main()
