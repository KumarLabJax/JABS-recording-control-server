"""
JWT Utilities.
"""

def add_claims_to_jwt(identity):
    """

    :param identity:
    :return:
    """
    claims = {
        # Issuer (JWT Standard)
        'iss': 'jax.ltm_control_service.api',
        # Subject (JWT Standard)
        'sub': 'Identity',
        'aud': identity.get('email'),
        # User ID
        'uid': identity.get('id')
    }

    return claims
