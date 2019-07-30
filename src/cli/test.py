"""
This is the testing cli entrypoint to the application
"""

import sys
import unittest
import logging

from os import path

from xmlrunner import XMLTestRunner
from flask_script import Command, Option


def run_tests(directory):
    """
    Load and run tests in the specified directory
    :param directory: The directory in which to look for tests
    :return: The test restults
    """
    tests = unittest.TestLoader().discover(directory, pattern='test*.py')
    return unittest.TextTestRunner(verbosity=2).run(tests)


class RunTestsCommand(Command):
    """
    Run all or some tests
    """

    option_list = (
        Option('--subdir', '-s', dest='directory', default=''),
    )

    """ Run unit tests """
    def run(self, directory):  # pylint: disable=E0202,W0221
        """ invoked by the command """
        logging.basicConfig(stream=sys.stderr)
        test_dir = path.join('src/test', directory)
        result = run_tests(test_dir)
        return 0 if result.wasSuccessful() else 1


class RunTestsXMLCommand(Command):
    """ Runs the unit tests specifically for bamboo CI/CD """

    def run(self): # pylint: disable=E0202
        """ invoked by the command """
        tests = unittest.TestLoader().discover('src/test', pattern='test*.py')
        result = XMLTestRunner(output='test-reports').run(tests)
        return 0 if result.wasSuccessful() else 1
