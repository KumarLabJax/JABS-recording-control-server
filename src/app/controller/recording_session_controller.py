"""
controller for interacting with recording sessions through the API
"""

from flask_restplus import Resource, Namespace, reqparse, abort, inputs
from flask_jwt_extended import jwt_required

import src.app.model as model
from .schemas import RECORDING_SESSION_SCHEMA, DEVICE_SESSION_STATUS, \
    NEW_RECORDING_SESSION_SCHEMA, DEVICE_SPECIFICATION_SCHEMA, add_models_to_namespace

NS = Namespace('recording-session',
               description='Endpoints for interacting with recording sessions')

__schemas = [
    RECORDING_SESSION_SCHEMA,
    DEVICE_SESSION_STATUS,
    NEW_RECORDING_SESSION_SCHEMA,
    DEVICE_SPECIFICATION_SCHEMA
]

NS = add_models_to_namespace(NS, __schemas)


@NS.route('')
class RecordingSession(Resource):
    """ Endpoint for recording sessions """

    get_parser = reqparse.RequestParser(bundle_errors=True)
    get_parser.add_argument(
        'archived', type=inputs.boolean, location='args', default=False,
        help=("If True get archived recording sessions.")
    )

    @jwt_required
    @NS.doc(security='JWT Access')
    @NS.marshal_with(RECORDING_SESSION_SCHEMA, as_list=True)
    @NS.expect(get_parser)
    def get(self):
        """
        get a list of recording sessions
        """

        args = RecordingSession.get_parser.parse_args()

        model.RecordingSession.check_for_complete()

        if args['archived'] is True:
            return model.RecordingSession.get_archived()
        else:
            return model.RecordingSession.get()

    @jwt_required
    @NS.doc(security='JWT Access')
    @NS.expect(NEW_RECORDING_SESSION_SCHEMA, validate=True)
    @NS.marshal_with(RECORDING_SESSION_SCHEMA)
    def post(self):
        """
        create new recording session
        """
        data = NS.payload

        bad_ids = []
        device_spec = []

        # check to see if the IDs are invalid
        for dev in data['device_spec']:
            if model.Device.get_by_id(dev['device_id']) is None:
                bad_ids.append(dev['device_id'])
            else:
                device_spec.append(dev)
        if len(bad_ids) > 0:
            abort(400, f"Invalid device IDs: {bad_ids}")

        fragment = data.get('fragment_hourly')

        session = model.RecordingSession.create(device_spec, data['duration'],
                                                data['name'], fragment,
                                                data['target_fps'],
                                                data['apply_filter'])
        return session


@NS.route('/<int:session_id>')
class RecordingSessionByID(Resource):
    """ Endpoint for interacting with a recording session specified by id """

    @jwt_required
    @NS.doc(security='JWT Access')
    @NS.response(404, "Recording session not found")
    @NS.marshal_with(RECORDING_SESSION_SCHEMA)
    def get(self, session_id):
        """
        return a recording session with a give session ID
        """
        return model.RecordingSession.get_by_id(session_id)

    delete_parser = reqparse.RequestParser(bundle_errors=True)
    delete_parser.add_argument(
        'archive', type=inputs.boolean, location='args', default=False,
        help=("Also archive the recording session.")
    )

    @jwt_required
    @NS.doc(security='JWT Access')
    @NS.response(204, "session archived")
    @NS.response(404, "recording session not found")
    @NS.expect(delete_parser)
    def delete(self, session_id):
        """
        cancel an active session if it is still running and optionally
        archive the session.
        :param session_id:
        :return: no content
        """

        args = RecordingSessionByID.delete_parser.parse_args()

        recording_session = model.RecordingSession.get_by_id(session_id)
        if recording_session is None:
            abort(404, "redcording session not found")

        recording_session.cancel()

        if args['archive']:
            recording_session.archive()
        return "", 204


@NS.route('/<int:session_id>/device-status/<int:device_id>')
class RecordingSessionDeviceStatus(Resource):
    """ Endpoint for getting a device's status for a session """

    @jwt_required
    @NS.doc(security='JWT Access')
    @NS.response(404, "recording session or device not found")
    @NS.marshal_with(DEVICE_SESSION_STATUS)
    def get(self, session_id, device_id):
        """
        return device's recording status for a recording session
        """
        device = model.Device.get_by_id(device_id)

        if not device:
            abort(404, "device not found")

        session = model.RecordingSession.get_by_id(session_id)

        if not session:
            abort(404, "session not found")

        return model.DeviceRecordingStatus.get(device, session)

    @jwt_required
    @NS.doc(security='JWT Access')
    @NS.response(404, "recording session or device not found")
    @NS.response(204, "success")
    def delete(self, session_id, device_id):
        """
        remove a device from a recording session
        """

        device = model.Device.get_by_id(device_id)

        if not device:
            abort(404, "device not found")

        session = model.RecordingSession.get_by_id(session_id)

        if not session:
            abort(404, "session not found")

        status = model.DeviceRecordingStatus.get(device, session)

        # this will remove the device from the session if it is pending or
        # recording. If the state is complete or failed, it has no effect
        status.remove_from_session()

        return "", 204
