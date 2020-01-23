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


@NS.route('/<int:uid>/change_password')
class UserPassword(Resource):

    @jwt_required
    @NS.doc(security='JWT Access')
    @NS.expect(PASSWORD_CHANGE_MODEL, validate=True)
    @NS.response(204, 'password changed')
    def put(self, uid):
        """
        change a user's password
        :return:
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
        except model.LTMSDatabaseException as e:
            abort(500, str(e))

        return '', 204


@NS.route('/invite_user')
class InviteUser(Resource):

    parser = reqparse.RequestParser(bundle_errors=True)
    parser.add_argument(
        'email', type=inputs.email(), location='args', required=True,
        help="Email address to send invitation to."
    )
    parser.add_argument(
        'admin', type=inputs.boolean, location='args', default=False,
        help="Give new user admin role?"
    )
    parser.add_argument(
        'url', type=inputs.url, location='args', required=True,
        help="URL for user to complete password reset."
    )

    __MESSAGE_TEMPLATE = Template(textwrap.dedent("""\
    <p>
    You have been invited to use the JAX Mouse Behavior Analysis control app.
    </p>
    
    <p>Please follow this link to set your password: ${URL}</p>
    """))

    @jwt_required
    @NS.doc(security='JWT Access')
    @NS.response(204, 'invitation sent')
    @NS.response(401, 'Unauthorized')
    @NS.expect(parser)
    def post(self):
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
            except model.LTMSDatabaseException:
                abort(400, 'unable to create user')
        else:
            new_user = False

        user_auth = model.SimpleAuth.get_user_auth(user.id)

        if not new_user:
            #resending invite, generate new password reset token
            try:
                user_auth.generate_reset_token()
            except model.LTMSDatabaseException:
                abort(400, 'unable to create password reset token')

        # send invitation
        email_notifier = EmailNotifier(
            smtp_server=flask.current_app.config['SMTP'],
            admin_email=flask.current_app.config['REPLY_TO']
        )
        url = urllib.parse.urljoin(args['url'], f"{user.id}/{user_auth.password_reset_token}")

        email_notifier.send(
            to=args['email'],
            message=self.__MESSAGE_TEMPLATE.substitute(URL=url),
            subject="JAX Mouse Behavior Analysis invitation"
        )

        return '', 204


@NS.route('/<int:uid>/reset_password/<token>')
class ResetPassword(Resource):

    @NS.expect(PASSWORD_RESET_MODEL)
    @NS.response(404, 'user not found')
    @NS.response(401, 'token not valid')
    @NS.response(204, 'password reset')
    def post(self, uid, token):
        user = model.User.get(uid)
        if not user:
            abort(404, 'user not found')

        user_auth = model.SimpleAuth.get_user_auth(user.id)

        if not user_auth.check_reset_token(token):
            abort(401, 'token not valid')

        if user_auth.token_is_expired():
            abort(401, 'token is expired')

        try:
            user_auth.update_password(NS.payload['password'])
        except model.PasswordFormatException as e:
            abort(400, e)
        return '', 204


@NS.route('/<int:uid>/send_reset')
class ResetPasswordRequest(Resource):
    parser = reqparse.RequestParser(bundle_errors=True)
    parser.add_argument(
        'url', type=inputs.url, location='args', required=True,
        help="URL for user to complete password reset."
    )

    __MESSAGE_TEMPLATE = Template(textwrap.dedent("""\
        <p>A password reset was requested for this email address.</p>

        <p>Please follow this link to set your password: ${URL}</p>
        
        <p>If you did not make this request, you can ignore this email.</p>
        """))

    @NS.response(400, 'unable to create password reset token')
    @NS.response(404, 'user not found')
    @NS.response(202, 'accepted')
    @NS.expect(parser)
    def post(self, uid):
        user = model.User.get(uid)
        if not user:
            abort(404, 'user not found')

        args = ResetPasswordRequest.parser.parse_args()

        user_auth = model.SimpleAuth.get_user_auth(user.id)
        try:
            user_auth.generate_reset_token()
        except model.LTMSDatabaseException:
            abort(400, 'unable to create password reset token')


        # generate URL for UI page to complete reset
        url = urllib.parse.urljoin(
            args['url'], f"?uid={user.id}&token={user_auth.password_reset_token}")
        # send invitation
        # send invitation
        email_notifier = EmailNotifier(
            smtp_server=flask.current_app.config['SMTP'],
            admin_email=flask.current_app.config['REPLY_TO']
        )
        email_notifier.send(
            to=user.email_address,
            message=self.__MESSAGE_TEMPLATE.substitute(URL=url),
            subject="JAX Mouse Behavior Analysis password reset"
        )

        return '', 202
