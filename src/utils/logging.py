"""
Utilities to help with logging
"""

import logging
import inspect

from flask.logging import wsgi_errors_stream

MODULE_FORMATTER = logging.Formatter(
    '[%(asctime)s] %(name)s %(levelname)s in %(module)s (l:%(lineno)d): %(message)s'
)

# We want a handler just like flask's but which shows more useful information for non-flask code
MODULE_HANDLER = logging.StreamHandler(wsgi_errors_stream)
MODULE_HANDLER.setFormatter(MODULE_FORMATTER)


def get_module_logger(string_identifier=None):
    """
    Get a logger for modules/services/controllers.
    :param string_identifier: What to call the logger. Logger name defaults to the relative
                               module name of the file it is called from if string_identifier
                               parameter isn't specified.
    :return: A logger instance
    """
    # If no string_identifier specified, use the name of the module the function was called from
    name = string_identifier or inspect.getmodule(inspect.stack()[1][0]).__name__
    return logging.getLogger(name)
