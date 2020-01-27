"""
controller for interacting with devices through the API
"""
import dateutil.parser
import json

from flask_jwt_extended import jwt_required
from flask_restplus import Resource, Namespace, abort

from .schemas import HEARTBEAT_SCHEMA, DEVICE_SCHEMA, SYSINFO_SCHEMA, \
    SENSOR_STATUS, CAMERA_STATUS, COMMAND_SCHEMA, \
    add_models_to_namespace
import src.app.model as model
from src.utils.exceptions import JaxMBAControlServiceException
from src.utils.logging import get_module_logger
from .utils.device_command import get_device_response

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
        except JaxMBAControlServiceException as err:
            abort(400, f"error processing heartbeat {err}")

        return get_device_response(device, data)


@NS.route('')
class DeviceList(Resource):
    """ Endpoint for interacting with lists of Devices """

    @jwt_required
    @NS.doc(security='JWT Access')
    @NS.marshal_with(DEVICE_SCHEMA, as_list=True)
    def get(self):
        """
        get list of known devices

        """
        return model.Device.get_devices()


@NS.route('/<int:device_id>')
class ByID(Resource):
    """ endpoint for getting a specific device by ID """

    @jwt_required
    @NS.doc(security='JWT Access')
    @NS.response(404, "Device not found")
    @NS.marshal_with(DEVICE_SCHEMA)
    def get(self, device_id):
        """ get a Device by ID """
        device = model.Device.get_by_id(device_id)
        return device if device else abort(404, f"Device {device_id} Not Found")


@NS.route('/<string:name>')
class ByName(Resource):
    """ endpoint for getting a specific device by a unique name """

    @jwt_required
    @NS.doc(security='JWT Access')
    @NS.response(404, "Device not found")
    @NS.marshal_with(DEVICE_SCHEMA)
    def get(self, name):
        """ get a Device by name """
        device = model.Device.get_by_name(name)
        return device if device else abort(404, f"Device {name} Not Found")



@NS.route('/stream/<int:device_id>')
class LiveStream(Resource):
    """endpoint for requesting live stream from device"""

    @jwt_required
    @NS.doc(security='JWT Access')
    @NS.response(404, "Device not found")
    @NS.response(500, "Unable to request live stream (internal server error)")
    @NS.response(503, "Live stream currently unavailable for device")
    @NS.response(200, "Live stream requested")
    def get(self, device_id):
        """
        Request that a device start (or continue) live stream.

        If the control server knows the device does not have an active recording
        session then a 503 (service unavailable) error will be returned,
        otherwise the request will be relayed to the device at its next status
        update.

        This should be called periodically when the stream is being watched.
        If, after a certain timeout (stream_keep_alive in the [MAIN] section of
        the config file), the server does not get a request for a stream then
        the device will stop the live stream to conserve network bandwidth.
        """
        device = model.Device.get_by_id(device_id)
        if not device:
            abort(404, f"Device {device_id} Not Found")

        try:
            device.request_live_stream()
        except model.JaxMBADatabaseException as e:
            abort(500, str(e))
        except JaxMBAControlServiceException:
            abort(503, f"Live stream currently unavailable for {device.name}")
