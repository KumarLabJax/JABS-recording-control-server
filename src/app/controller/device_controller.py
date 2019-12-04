"""
controller for interacting with devices through the API
"""
import dateutil.parser
from flask_restplus import Resource, Namespace, reqparse, abort
from .schemas import HEARTBEAT_SCHEMA, DEVICE_SCHEMA, SYSINFO_SCHEMA, \
    SENSOR_STATUS, CAMERA_STATUS, COMMAND_SCHEMA, \
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
    COMMAND_SCHEMA
]
NS = add_models_to_namespace(NS, models)

LOGGER = get_module_logger()


@NS.route('/heartbeat')
class DeviceHeartbeat(Resource):
    """ Endpoint for device heartbeats """

    @NS.response(200, "success, no action")
    @NS.response(204, "success, action")
    @NS.expect(HEARTBEAT_SCHEMA, validate=True)
    @NS.marshal_with(COMMAND_SCHEMA)
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
                release=data['system_info']['release'],
                location=data.get('location')
            )
        except LTMSControlServiceException as err:
            abort(400, f"error processing heartbeat {err}")

        # get session ID included in message if present
        client_session = data.get('session_id')

        # has the device been assigned to a recording session?
        if device.session_id:

            device_session_status = model.DeviceRecordingStatus.get(device, device.recording_session)

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
                    # we were waiting to hear from device to tell it to start
                    return {
                               'command_name': "START",
                               'parameters': json.dumps({
                                   'session_id': device.session_id,
                                   'duration': device.recording_session.duration,
                                   'fragment_hourly': device.recording_session.fragment_hourly,
                                   'file_prefix': device_session_status.file_prefix,
                                   'target_fps': device.recording_session.target_fps,
                                   'apply_filter': device.recording_session.apply_filter
                               })
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
                    # device is unexpectedly idle after it had previously
                    # joined the recording session.
                    try:
                        device_session_status.update_status(
                            model.DeviceRecordingStatus.Status.FAILED,
                            "device unexpectedly left recording session"
                        )
                        device.clear_session()
                    except LTMSControlServiceException:
                        # couldn't update the status for some reason
                        # don't treat this as fatal, we'll try again next time
                        pass

            else:
                # device already knows it is part of a session
                # update its state accordingly

                # extra sanity check
                if device.session_id != client_session:
                    # device and server are confused.
                    # tell device to stop what it is doing
                    return {'command_name': "STOP"}, 200

                if not data['sensor_status']['camera']['recording']:
                    # device is no longer recording

                    # check to see if there was an error
                    err_msg = data.get('err_msg')

                    try:
                        if err_msg:
                            # handle error case
                            device_session_status.update_status(
                                model.DeviceRecordingStatus.Status.FAILED,
                                err_msg
                            )
                        else:
                            # no error, this means the device finished recording
                            duration = data['sensor_status']['camera'].get('duration', 0)
                            device_session_status.update_recording_time(
                                duration)
                            if device_session_status.status == model.DeviceRecordingStatus.Status.RECORDING:
                                device_session_status.update_status(
                                    model.DeviceRecordingStatus.Status.COMPLETE
                                )

                        device.clear_session()
                        return {'command_name': "COMPLETE"}, 200

                    except LTMSControlServiceException:
                        # couldn't update the device for some reason
                        # don't treat this as fatal. we will try again next time
                        # device sends us a status update
                        pass

                elif device_session_status.status == model.DeviceRecordingStatus.Status.CANCELED:
                    # we have a cancel request for this device,
                    # tell it to stop recording
                    return {'command_name': "STOP"}, 200
                elif device_session_status.status == model.DeviceRecordingStatus.Status.RECORDING:
                    # device is recording, update our recording status with
                    # the current recording duration
                    try:
                        device_session_status.update_recording_time(data['sensor_status']['camera']['duration'])
                    except LTMSControlServiceException:
                        # couldn't update the device time for some reason
                        # don't treat this as fatal.
                        pass
                elif device_session_status.status == model.DeviceRecordingStatus.Status.PENDING:
                    # device is sending first update after joining the session
                    try:
                        device.join_session(
                            device_session_status.session)
                    except LTMSControlServiceException as err:
                        abort(400, f"error joining session {err}")

                    try:
                        device_session_status.update_recording_time(
                            data['sensor_status']['camera']['duration'])
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
