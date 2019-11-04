"""
controller for interacting with devices through the API
"""
import dateutil.parser
from flask_restplus import Resource, Namespace, reqparse, abort
from .schemas import HEARTBEAT_SCHEMA, DEVICE_SCHEMA, SYSINFO_SCHEMA, \
    SENSOR_STATUS, CAMERA_STATUS, HEARTBEAT_REPLY_SCHEMA, COMMAND_SCHEMA, \
    add_models_to_namespace
import json
import src.app.model as model
from src.utils.exceptions import LTMSControlServiceException
from src.utils.logging import get_module_logger

NS = Namespace('device',
               description='Endpoints for interacting with devices')
models = [
    DEVICE_SCHEMA,
    HEARTBEAT_SCHEMA,
    SYSINFO_SCHEMA,
    SENSOR_STATUS,
    CAMERA_STATUS,
    HEARTBEAT_REPLY_SCHEMA,
    COMMAND_SCHEMA
]
NS = add_models_to_namespace(NS, models)

LOGGER = get_module_logger()

@NS.route('/heartbeat')
class DeviceHeartbeat(Resource):
    """ Endpoint for device heartbeats """

    @NS.response(204, "success, no action")
    @NS.response(204, "success, action")
    @NS.expect(HEARTBEAT_SCHEMA, validate=True)
    @NS.marshal_with(HEARTBEAT_REPLY_SCHEMA)
    def post(self):
        data = NS.payload
        device = None
        try:
            timestamp = dateutil.parser.parse(data['timestamp'])
        except ValueError:
            abort(400, f"unable to parse timestamp: {data['timestamp']}")

        try:
            device = model.Device.update_from_heartbeat(
                name=data['name'],
                state=model.Device.State[data['state']],
                last_update=timestamp,  # pylint: disable=E0601
                uptime=data['system_info']['uptime'],
                total_ram=data['system_info']['total_ram'],
                free_ram=data['system_info']['free_ram'],
                load=data['system_info']['load'],
                sensor_status=json.dumps(data['sensor_status']),
                total_disk=data['system_info']['total_disk'],
                free_disk=data['system_info']['free_disk'],
                release=data['system_info']['release']
            )
        except LTMSControlServiceException as err:
            abort(400, f"error processing heartbeat {err}")

        # has the device been assigned to a recording session?
        if device.session_id:
            client_session = data.get('session_id')
            device_session_status = model.DeviceRecordingStatus.get_for_device(device)

            # this is an extra sanity check
            if not device_session_status:
                # device has a session id associated with it in the database,
                # but it doesn't have a corresponding row in
                # DeviceRecordingStatus
                LOGGER.error(f"device doesn't have corresponding DeviceRecordingStatus for session {device.session_id}")
                try:
                    device.clear_session()
                except LTMSControlServiceException:
                    # for now pass, it should try again next heartbeat
                    pass
                return '', 204

            # device doesn't know it's been assigned to the session yet
            if not client_session:
                if device_session_status.status == model.DeviceRecordingStatus.Status.PENDING:
                    return {
                               'commands': [
                                   {
                                       'command': "START",
                                       'parameters': json.dumps({
                                           'session_id': device.session_id,
                                           'duration': device.recording_session.duration,
                                           'fragment_hourly': device.recording_session.fragment_hourly,
                                           'file_prefix': device.recording_session.file_prefix
                                       })
                                   }
                               ]
                           }, 200
                elif device_session_status.status == model.DeviceRecordingStatus.Status.CANCELED:
                    # device appears to have successfully canceled, clear its
                    # active session so it is available to be included in a
                    # new session
                    try:
                        device.clear_session()
                    except LTMSControlServiceException:
                        # for now pass, it should try again next heartbeat
                        pass
                    return '', 204
                else:
                    # device doesn't think it's part of the session, but the
                    # status is not PENDING in the database.
                    # This could have been a device crash/reboot.
                    try:
                        device_session_status.update_status(
                            model.DeviceRecordingStatus.Status.FAILED,
                            "Device Error: possible reboot?"
                        )
                    except LTMSControlServiceException:
                        # couldn't update the status for some reason
                        # don't treat this as fatal, we'll try again next time
                        pass

            else:
                # device already knows it is part of a session

                # extra sanity check
                if device.session_id != client_session:
                    # device and server are confused.
                    # tell device to stop what it is doing
                    return {'commands': [{'command': "CANCEL"}]}, 200

                # device has previously joined the recording session
                if device_session_status.status == model.DeviceRecordingStatus.Status.CANCELED:
                    # we have a cancel request for this device,
                    # tell it to stop recording
                    return {'commands': [{'command': "CANCEL"}]}, 200
                elif device_session_status.status == model.DeviceRecordingStatus.Status.RECORDING:
                    # device is recording, update our recording status with
                    # the current recording duration
                    try:
                        device_session_status.update_recording_time(data['sensor_status']['camera']['duration'])
                    except LTMSControlServiceException:
                        # couldn't update the device time for some reason
                        # don't treat this as fatal.
                        pass

        return '', 204


@NS.route('')
class DeviceList(Resource):
    """ Endpoint for interacting with lists of Devices """

    get_parser = reqparse.RequestParser()
    get_parser.add_argument('state', location='args',
                            choices=[s.name for s in model.Device.State],
                            help="Only return devices with this state.")

    @NS.expect(get_parser, validate=True)
    @NS.marshal_with(DEVICE_SCHEMA, as_list=True)
    def get(self):
        """
        get device

        can include an optional state string to filter
        """
        args = self.get_parser.parse_args(strict=True)
        params = {}

        if args['state'] is not None:
            params['state'] = model.Device.State[args.state]

        return model.Device.get_devices(**params)


@NS.route('/<int:device_id>')
class ByID(Resource):
    """ endpoint for getting a specific device by ID """

    @NS.response(404, "Device not found")
    @NS.marshal_with(DEVICE_SCHEMA)
    def get(self, device_id):
        """ get a Device by ID """
        device = model.Device.get_by_id(device_id)
        return device if device else abort(404, f"Device {device_id} Not Found")


@NS.route('/<string:name>')
class ByName(Resource):
    """ endpoint for getting a specific device by a unique name """

    @NS.response(404, "Device not found")
    @NS.marshal_with(DEVICE_SCHEMA)
    def get(self, name):
        """ get a Device by name """
        device = model.Device.get_by_name(name)
        return device if device else abort(404, f"Device {name} Not Found")
