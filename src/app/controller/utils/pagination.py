"""
Controller Pagination Utilities
"""

from functools import wraps
from flask_restplus import reqparse


def add_pagination_args(parser):
    """
    Add pagination args to a parser
    :param parser: Initialized parser to add args to
    :return:
    """
    parser.add_argument('page', type=int, help='Which page to display', default=1, required=False)
    parser.add_argument('per_page', type=int, help='Items per page', default=50, required=False)
    return parser


def get_pagination_args(parsed_args):
    """
    Get pagination args from parsed args
    :param parsed_args: parsed pagination args
    :return: tuple (page, per_page)
    """
    page = parsed_args['page'] if parsed_args['page'] else 0
    per_page = parsed_args['per_page'] if parsed_args['per_page'] else 50
    return page, per_page


PAGINATION_PARSER = add_pagination_args(reqparse.RequestParser())


def parse_pagination_args(fnc):
    """
    Parse url query parameters 'page' and 'per_page' and add to request kwargs
    :param fnc:
    :return:
    """
    @wraps(fnc)
    def wrapper(*args, **kwargs):
        parser = PAGINATION_PARSER
        page, per_page = get_pagination_args(parser.parse_args())
        kwargs = {
            'page': page,
            'per_page': per_page,
            **kwargs
        }
        return fnc(*args, **kwargs)
    return wrapper
