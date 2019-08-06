""" Tests related to the flask server"""

import unittest
import requests

from src.test import BaseLiveServerTestCase


class SmokeTest(BaseLiveServerTestCase):
    """ Is the server turning on and responding? """

    def test_app_turns_on(self):
        """ Does the flask app turn on? """
        response = requests.get(self.get_server_url())
        self.assertEqual(response.status_code, 200)

    #def test_hello(self):
    #    """ Can we reach a known endpoint? """
    #    uri = self.get_server_url() + url_for('api.hello_hello_world')
    #    response = requests.get(uri)
    #    self.assertEqual(response.json(), dict(message="Hello World!"))


if __name__ == '__main__':
    unittest.main()
