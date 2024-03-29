import textwrap
from string import Template
import urllib.parse

import flask
from flask_jwt_extended import jwt_required, get_jwt_identity
from flask_restplus import Resource, Namespace, fields, abort, reqparse, inputs

import src.app.model as model
from src.utils.logging import get_module_logger
from src.utils.email_notification import EmailNotifier


NS = Namespace('user',
               description='Endpoints for interacting with users')

LOGGER = get_module_logger()

PASSWORD_CHANGE_MODEL = NS.model('password_change', {
    'old_password': fields.String(required=True),
    'new_password': fields.String(required=True)
})

PASSWORD_RESET_MODEL = NS.model('password_reset', {
    'password': fields.String(required=True)
})

PASSWORD_RESET_REQUEST_MODEL = NS.model('request_password_reset', {
    'email': fields.String(required=True),
    'url': fields.Url(required=True)
})


@NS.route('/<int:uid>/change_password')
class UserPassword(Resource):
    """
    route for a user to manage their password
    """

    @jwt_required
    @NS.doc(security='JWT Access')
    @NS.expect(PASSWORD_CHANGE_MODEL, validate=True)
    @NS.response(204, 'password changed')
    @NS.response(403, 'identity in jwt token does not match uid')
    def put(self, uid):
        """
        change a user's password
        """
        identity = get_jwt_identity()
        if identity['uid'] != uid:
            abort(403, "not authorized")

        payload = NS.payload

        auth_data = model.SimpleAuth.get_user_auth(uid)

        # payload has to contain the user's old password just to double check
        if not auth_data.check_password(payload['old_password']):
            abort(400, "current password does not match")

        try:
            model.SimpleAuth.update_password(auth_data, payload['new_password'])
        except model.PasswordFormatException as e:
            abort(400, str(e))
        except model.JaxMBADatabaseException as e:
            abort(500, str(e))

        return '', 204


@NS.route('/invite')
class InviteUser(Resource):
    """
    Invite a user to use the app.
    """

    parser = reqparse.RequestParser(bundle_errors=True)
    parser.add_argument(
        'email', type=inputs.email(), location='json', required=True,
        help="Email address to send invitation to."
    )
    parser.add_argument(
        'admin', type=inputs.boolean, location='json', default=False,
        help="Give new user admin role?"
    )
    parser.add_argument(
        'url', type=inputs.url, location='json', required=True,
        help="URL for user to complete password reset."
    )

    __MESSAGE_TEMPLATE = Template(textwrap.dedent("""\
    <p>
    You have been invited to use the JAX Mouse Behavior Analysis control app.
    </p>
    
    <p>Please follow this link to set your password: ${URL}</p>
    
    <p>This link will expire in ${EXP} hours.</p>
    """))

    @jwt_required
    @NS.doc(security='JWT Access')
    @NS.response(204, 'invitation sent')
    @NS.response(401, 'Unauthorized')
    @NS.expect(parser)
    def post(self):
        """
        Send an invitation to a user identified by email address.

        If the user does not exist, they will be added to the database. For both
        new and existing users a password reset token will be generated and
        emailed to them.

        This endpoint requires admin privs.
        """

        identity = get_jwt_identity()
        current_user = model.User.get(identity['uid'])
        new_user = True

        if not current_user.admin:
            abort(401, 'You are unauthorized to perform this action')

        args = InviteUser.parser.parse_args()

        # check to see if user already exists
        user = model.User.lookup(args['email'])

        if not user:
            # user does not already exist, create
            try:
                user = model.SimpleAuth.create_user(args['email'], admin=args['admin'])
            except model.JaxMBADatabaseException:
                abort(400, 'unable to create user')
        else:
            new_user = False

        user_auth = model.SimpleAuth.get_user_auth(user.id)

        if not new_user:
            #resending invite, generate new password reset token
            try:
                user_auth.generate_reset_token()
            except model.JaxMBADatabaseException:
                abort(400, 'unable to create password reset token')

        # send invitation
        email_notifier = EmailNotifier(
            smtp_server=flask.current_app.config['SMTP'],
            admin_email=flask.current_app.config['REPLY_TO']
        )
        url = urllib.parse.urljoin(args['url'] + '/', f"{user.id}/{user_auth.password_reset_token}")

        try:
            email_notifier.send(
                to=args['email'],
                message=self.__MESSAGE_TEMPLATE.substitute(
                    URL=url,
                    EXP=model.simple_auth_model.RESET_TOKEN_VALID_DAYS * 24
                ),
                subject="JAX Mouse Behavior Analysis invitation"
            )
        except Exception as e:
            abort(400, f"Error sending email")

        return '', 204


@NS.route('/<int:uid>/reset_password/<token>')
class ResetPassword(Resource):
    """
    route for resetting password
    """

    @NS.expect(PASSWORD_RESET_MODEL)
    @NS.response(404, 'user not found')
    @NS.response(401, 'token not valid')
    @NS.response(204, 'password reset')
    def post(self, uid, token):
        """
        Reset a user password. Requires a token, which would have been emailed
        to the the user.

        :param uid: id of user resetting password
        :param token: password reset token
        """

        user = model.User.get(uid)
        if not user:
            abort(404, 'user not found')

        user_auth = model.SimpleAuth.get_user_auth(user.id)

        # does the reset token match the most recently generated
        if not user_auth.check_reset_token(token):
            abort(401, 'token not valid')

        # has the token expired?
        if user_auth.token_is_expired():
            abort(401, 'token is expired')

        # everything checks out, try to update the password
        try:
            user_auth.update_password(NS.payload['password'])
        except model.PasswordFormatException as e:
            abort(400, e)
        return '', 204


@NS.route('/send_pw_reset')
class ResetPasswordRequest(Resource):
    """
    route for requesting a password reset token
    """

    __MESSAGE_TEMPLATE = Template(textwrap.dedent("""\
        <p>A password reset was requested for this email address.</p>

        <p>Please follow this link to set your password: ${URL}</p>
        
        <p>This link will expire in ${EXP} hours.</p>
        
        <p>If you did not make this request, you can ignore this email.</p>
        """))

    @NS.response(202, 'accepted')
    @NS.response(500, 'server error')
    @NS.expect(PASSWORD_RESET_REQUEST_MODEL, validate=True)
    def post(self):
        """
        request a password reset token by email

        This endpoint is used to initiate the password reset process if a user
        does not remember their password. The user submits the request with
        their email address. If the email address matches an existing user we
        send an email to them with a link containing a password reset token with
        a limited lifespan. The user can follow the link and set a new password.
        """
        user = model.User.lookup(NS.payload['email'])

        # don't let the requester know the email address is not valid to
        # prevent fishing for valid accounts
        if not user:
            return '', 202

        user_auth = model.SimpleAuth.get_user_auth(user.id)
        try:
            user_auth.generate_reset_token()
        except model.JaxMBADatabaseException:
            abort(500, 'unable to create password reset token')

        # generate URL for UI page to complete reset
        url = urllib.parse.urljoin(
            NS.payload['url'] + '/',
            f"{user.id}/{user_auth.password_reset_token}"
        )
        # send invitation
        email_notifier = EmailNotifier(
            smtp_server=flask.current_app.config['SMTP'],
            admin_email=flask.current_app.config['REPLY_TO']
        )

        try:
            email_notifier.send(
                to=user.email_address,
                message=self.__MESSAGE_TEMPLATE.substitute(
                    URL=url,
                    EXP=model.simple_auth_model.RESET_TOKEN_VALID_DAYS * 24
                ),
                subject="JAX Mouse Behavior Analysis password reset"
            )
        except:
            abort(500, "unable to send email")

        return '', 202
