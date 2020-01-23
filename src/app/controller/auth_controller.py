"""
An example of how to provide basic (username,password) style auth
"""
from flask_restplus import Resource, Namespace, fields, abort
from flask_jwt_extended import create_access_token, create_refresh_token, \
    jwt_refresh_token_required, get_jwt_identity

from src.app.model.simple_auth_model import SimpleAuth
from src.utils.exceptions import CredentialError

NS = Namespace('auth')

TOKEN_MODEL = NS.model('tokens', {
    'refresh': fields.String(),
    'access': fields.String(),
})

TOKEN_FLOW_MODEL = NS.model('token_flow', {
    'auth_uri': fields.String(skip_none=True),
    'tokens': fields.Nested(TOKEN_MODEL, skip_none=True)
})

CREDENTIAL_MODEL = NS.model('credentials', {
    'email_address': fields.String(required=True),
    'password': fields.String(required=True, format='password')
})


@NS.route('/login', methods=['POST'])
class UserLogin(Resource):
    """ Get access tokens """

    @NS.expect(CREDENTIAL_MODEL, validate=True)
    @NS.marshal_with(TOKEN_MODEL)
    def post(self):
        """ Authenticate and create jwt """
        payload = NS.payload
        user = None

        # Authenticate User
        #
        try:
            user = SimpleAuth.authenticate(payload['email_address'], payload['password'])
        except CredentialError:
            abort(401, message=str("unable to authenticate user"))

        identity = {
            'uid': user.id,
            'email_address': user.email_address
        }

        access_token = create_access_token(identity=identity)
        # Here the refresh token uses an identity that is identical to the access.
        # Often we will only use the minimum information we would need to fetch
        # the users identity when creating a new access token
        refresh_token = create_refresh_token(identity=identity)

        return {
            'access': access_token,
            'refresh': refresh_token
        }


@NS.route('/refresh', methods=['POST'])
class UserRefresh(Resource):
    """ Get access token from refresh """

    @staticmethod
    @jwt_refresh_token_required
    @NS.doc(security='JWT Refresh')
    def post():
        """ Create a new access token from a refresh token """

        identity = get_jwt_identity()

        # If the refresh token identity is not identical to the access token identity
        # (see /login route above), we need to first get the user's full identity
        # before creating a new access token.
        # e.g. full_identity = example_get_full_id(user_id=identity['uid'])

        return {
            'access': create_access_token(identity=identity)
        }
