"""
Factories for the falsk app and the celery app
"""

import logging

from flask import Flask
from flask_cors import CORS
from flask_migrate import Migrate

from src.config import CONFIG_BY_NAME, DEFAULT_CONFIG
from src.app.model import MA, init_db, BASE


def create_app(config_name=None, app=None, config_object=None):
    """
    Create an instance of a flask app
    :param config_name: the name of the config to use
    :param app: existing app if initialized
    :param config_object: Config object that will override config name
    :return:
    """
    conf = config_object or CONFIG_BY_NAME.get(config_name, DEFAULT_CONFIG)
    logging.basicConfig(level=conf.LOG_LEVEL)
    app = app or Flask(__name__, static_url_path='/static', static_folder='static')
    app.config.from_object(conf)
    app.app_context().push()
    with app.app_context():
        Migrate(app, BASE)
        MA.init_app(app)
        app.config['db_engine'] = init_db(app)
        CORS(app)

    return app
