"""
This is the manager entrypoint to the application
"""

import os
from flask_script import Manager
from flask_migrate import MigrateCommand

from src.app import create_app
from src.cli.run import RunCommand, GunicornRunCommand
from src.cli.test import RunTestsCommand, RunTestsXMLCommand
from src.cli.config import GenerateSecretsCommand, InitConfigCommand
from src.cli.user import CreateAdmin

MANAGER = Manager(create_app(os.getenv('FLASK_CONFIG') or 'dev'))

# Run the application
MANAGER.add_command('run', RunCommand())
MANAGER.add_command('gunicorn_run', GunicornRunCommand())

# Create initial admin user
MANAGER.add_command('create_admin', CreateAdmin())

# Perform database operations
MANAGER.add_command('db', MigrateCommand)

# Manage the 'jax-mba-service.config' file
MANAGER.add_command('create_secrets', GenerateSecretsCommand)
MANAGER.add_command('init_config', InitConfigCommand)

# Run tests
MANAGER.add_command('test', RunTestsCommand())
MANAGER.add_command('test_xml', RunTestsXMLCommand())


if __name__ == '__main__':
    MANAGER.run()
