"""
Password input for swagger docs
"""
def password_input(value):
    """
    Custom password input to hide values in swagger form
    :param value: The input value
    :return: The same value
    """
    return value


password_input.__schema__ = {'type': 'string', 'format': 'password'}
