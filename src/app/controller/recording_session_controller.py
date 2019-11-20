"""
controller for interacting with recording sessions through the API
"""

from flask_restplus import Resource, Namespace, reqparse, abort, inputs

import src.app.model as model
from .schemas import RECORDING_SESSION_SCHEMA, DEVICE_SESSION_STATUS, \
    RECORDING_SESSION_HISTORY_SCHEMA, NEW_RECORDING_SESSION_SCHEMA, add_models_to_namespace

NS = Namespace('recording-session',
               description='Endpoints for interacting with recording sessions')

__schemas = [
    RECORDING_SESSION_SCHEMA,
    DEVICE_SESSION_STATUS,
    NEW_RECORDING_SESSION_SCHEMA,
    RECORDING_SESSION_HISTORY_SCHEMA
]

NS = add_models_to_namespace(NS, __schemas)


@NS.route('')
class RecordingSession(Resource):
    """ Endpoint for recording sessions """

    @NS.marshal_with(RECORDING_SESSION_SCHEMA, as_list=True)
    def get(self):
        """
        get a list of active recording sessions
        """
        return model.RecordingSession.get()

    @NS.expect(NEW_RECORDING_SESSION_SCHEMA, validate=True)
    @NS.marshal_with(RECORDING_SESSION_SCHEMA)
    def post(self):
        """
        create new recording session
        """
        data = NS.payload

        bad_ids = []
        device_ids = []

        # check to see if the IDs are invalid
        for device_id in data['device_ids']:
            if model.Device.get_by_id(device_id) is None:
                bad_ids.append(device_id)
            else:
                device_ids.append(device_id)
        if len(bad_ids) > 0:
            abort(400, f"Invalid device IDs: {bad_ids}")

        prefix = data.get('file_prefix', "")
        fragment = data.get('fragment_hourly')
        notes = data.get('notes')

        session = model.RecordingSession.create(device_ids, data['duration'],
                                                data['name'], fragment,
                                                data['target_fps'],
                                                data['apply_filter'],
                                                file_prefix=prefix,
                                                notes=notes)
        return session


@NS.route('/<int:session_id>')
class RecordingSessionByID(Resource):
    """ Endpoint for interacting with a recording session specified by id """

    @NS.response(404, "Recording session not found")
    @NS.marshal_with(RECORDING_SESSION_SCHEMA)
    def get(self, session_id):
        """
        return a recording session with a give session ID
        """
        return model.RecordingSession.get_by_id(session_id)


@NS.route('/<int:session_id>/device-status/<int:device_id>')
class RecordingSessionDeviceStatus(Resource):
    """ Endpoint for getting a device's status for a session """

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


@NS.route('/history')
class RecordingSessionHistory(Resource):
    """ Endpoint for getting information about previous recording sessions """

    get_parser = reqparse.RequestParser(bundle_errors=True)
    get_parser.add_argument(
        'start_date', type=inputs.date, location='args', default=None,
        help="get recording sessions created on or after this date"
    )
    get_parser.add_argument(
        'end_date', type=inputs.date, location='args', default=None,
        help="get recording sessions created on or before this date"
    )

    @NS.marshal_with(RECORDING_SESSION_HISTORY_SCHEMA, as_list=True)
    @NS.expect(get_parser)
    def get(self):
        """
        get list of previous (no longer active) recording sessions

        can specify optional start and/or end dates
        """

        args = RecordingSessionHistory.get_parser.parse_args()
        return model.RecordingSessionHistory.get(args['start_date'], args['end_date'])
