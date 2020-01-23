"""
Base exceptions namespace for the app
"""


class LTMSControlServiceException(Exception):
    """
    Base exception for the Long-Term Monitoring System Control Service app
    """


class CredentialError(LTMSControlServiceException):
    """ user not found in database """
