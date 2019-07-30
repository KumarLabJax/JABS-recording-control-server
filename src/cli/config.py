"""
Starts the dev server
"""

from flask_script import Command
from src.utils.config_tools import create_empty_config, generate_secrets


class GenerateSecretsCommand(Command):
    """
    If not yet set, set the secret keys in config.ini to randomly generated 32bit hex values
    :return: None
    """

    def run(self):  # pylint: disable=E0202
        """ invoked by the command """
        generate_secrets()


class InitConfigCommand(Command):
    """
    Overwrite current config with blank one, or create new config if there is none,
     then generate config secrets
    :return: None
    """

    def run(self):  # pylint: disable=E0202
        """ invoked by the command """
        create_empty_config()
        generate_secrets()
