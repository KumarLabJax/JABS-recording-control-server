"""
Base exceptions namespace for the app
"""


class JaxMBAControlServiceException(Exception):
    """
    Base exception for the JAX Mouse Behavior Analysis Control Service app
    """


class CredentialError(JaxMBAControlServiceException):
    """ user not found in database """
