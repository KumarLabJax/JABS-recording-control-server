"""
Base classes for use in the testing scripts
"""

# This next line disables checking that attributes are defined outside init
#   Overriding init for TestCase breaks the library
# pylint: disable=W0201

from flask_testing import TestCase, LiveServerTestCase
from src.app import create_app
from src.app.model import SESSION, drop_all


class BaseTestCase(TestCase):
    """ Base Tests """
    __config_name__ = 'test'

    # TODO: Figure out how to set a specific url to test against
    #  as a CLI argument to starting the tests
    def create_app(self):
        app = create_app(self.__config_name__)
        app.config['PRESERVE_CONTEXT_ON_EXCEPTION'] = False
        self.engine = app.config['db_engine']
        self.session = SESSION
        return app


class BaseDBTestCase(BaseTestCase):
    """ DB Test Specific Base Case """

    def tearDown(self):
        self.session.remove()
        drop_all(self.engine)


class BaseLiveServerTestCase(LiveServerTestCase):
    """ Base Tests that require a live server """
    __config_name__ = 'test'

    def create_app(self):
        app = create_app(self.__config_name__)
        app.config['LIVESERVER_PORT'] = 0
        app.config['LIVESERVER_TIMEOUT'] = 10
        app.config['PRESERVE_CONTEXT_ON_EXCEPTION'] = False
        self.engine = app.config['db_engine']
        self.session = SESSION
        return app
