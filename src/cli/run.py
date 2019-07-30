"""
Starts the dev server
"""

from flask_script import Command
from src import APP
from .utils import start_subprocess_and_wait


class RunCommand(Command):
    """
    The main entrypoint to running the app
    :return: None
    """

    def run(self):  # pylint: disable=E0202
        """ invoked by the command """
        APP.run()


class GunicornRunCommand(Command):
    """
    Gunicorn version of RunCommand for use in the docker container
    """

    def run(self):  # pylint: disable=E0202
        gunicorn_command = 'gunicorn -b 0.0.0.0:8000 wsgi:application'
        start_subprocess_and_wait(gunicorn_command)
