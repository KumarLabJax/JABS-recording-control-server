"""
Tests the various configuration environments
"""

import unittest
from pylint import epylint as lint

from src.test import BaseTestCase


def lint_module(module_path, options='--disable=W0511'):
    """ helper function to enable drying the lint tests """
    stdout, _ = lint.py_run(f'{module_path} {options}', return_std=True)
    stdout_string = stdout.getvalue()
    code_passes = 'Your code has been rated at 10.00/10' in stdout_string
    return code_passes, stdout_string


class TestLintCode(BaseTestCase):
    """ Perform linting analysis on the source code """

    def test_lint_src(self):
        """ Lint the entire source and check for problems """
        code_passes, stdout = lint_module('src/')
        self.assertTrue(code_passes, stdout)

    def test_lint_controllers(self):
        """ Lint the controllers and check for problems """
        code_passes, stdout = lint_module('src/app/controller/')
        self.assertTrue(code_passes, stdout)

    def test_lint_models(self):
        """ Lint the models and check for problems """
        code_passes, stdout = lint_module('src/app/model/')
        self.assertTrue(code_passes, stdout)

    def test_lint_services(self):
        """ Lint the services and check for problems """
        code_passes, stdout = lint_module('src/app/service/')
        self.assertTrue(code_passes, stdout)

    def test_lint_tests(self):
        """ Lint the tests and check for problems """
        code_passes, stdout = lint_module('src/test/')
        self.assertTrue(code_passes, stdout)


if __name__ == '__main__':
    unittest.main()
