"""
JWT Utilities for Controller
"""
from functools import wraps
from flask_jwt_extended import verify_jwt_in_request, get_jwt_claims, verify_jwt_in_request_optional
from src.utils.exceptions import JaxMBAControlServiceException


AUTHORIZATIONS = {
    'JWT Access': {
        'type': 'apiKey',
        'in': 'header',
        'name': 'Authorization'
    },
    'JWT Refresh': {
        'type': 'apiKey',
        'in': 'header',
        'name': 'Authorization'
    },
}


class UrlJwtMismatch(JaxMBAControlServiceException):
    """
    Url and jwt don't agree about something
    """


def required_jwt_matches_url(url_path_param, claim_key):
    """
    Identical to @jwt_required, but also takes a url_path_param key and
    claim key that are use to check that the value passed for each match.
    This is useful for user specific routes where the user id in the url
    always needs to match the id in the token.
    :param url_path_param: the name of the url param to match
    :param claim_key: the name of the jwt claim to match
    :return:
    """
    def meta_warp(fnc):
        @wraps(fnc)
        def wrapper(*args, **kwargs):
            verify_jwt_in_request()
            claims = get_jwt_claims()
            if kwargs.get(url_path_param) != claims[claim_key]:
                raise UrlJwtMismatch('Route requires access token match url')
            return fnc(*args, **kwargs)
        return wrapper
    return meta_warp


def optional_jwt_matches_url(url_path_param, claim_key):
    """
    Identical to @required_jwt_matches_url, but does not require a jwt.
    This is useful for requiring that when a jwt is passed or
    url_path_param provided, that they match.
    :param url_path_param:
    :param claim_key:
    :return:
    """
    def meta_warp(fnc):
        @wraps(fnc)
        def wrapper(*args, **kwargs):
            verify_jwt_in_request_optional()
            claims = get_jwt_claims()
            if kwargs.get(url_path_param) != claims.get(claim_key):
                raise UrlJwtMismatch('Route requires access token match url')
            return fnc(*args, **kwargs)
        return wrapper
    return meta_warp


def jwt_admin_required(fnc):
    """
    Decorator that validates that the claim for 'role' in the request
    jwt is 'admin'
    :param fnc:
    :return:
    """
    @wraps(fnc)
    def wrapper(*args, **kwargs):
        verify_jwt_in_request()
        claims = get_jwt_claims()
        if claims['role'] != 'admin':
            raise UrlJwtMismatch('Route requires admin privileges')
        return fnc(*args, **kwargs)
    return wrapper
