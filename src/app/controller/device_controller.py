"""
controller for interacting with devices through the API
"""
import dateutil.parser
from flask_restplus import Resource, Namespace, reqparse, abort
from .schemas import HEARTBEAT_SCHEMA, DEVICE_SCHEMA, SYSINFO_SCHEMA, \
    SENSOR_STATUS, CAMERA_STATUS, add_models_to_namespace
import json
import src.app.model as model
from src.utils.exceptions import LTMSControlServiceException

NS = Namespace('device',
               description='Endpoints for interacting with devices')
models = [
    DEVICE_SCHEMA,
    HEARTBEAT_SCHEMA,
    SYSINFO_SCHEMA,
    SENSOR_STATUS,
    CAMERA_STATUS
]
NS = add_models_to_namespace(NS, models)


@NS.route('/heartbeat')
class DeviceHeartbeat(Resource):
    """ Endpoint for device heartbeats """

    @NS.response(204, "success, no command")
    @NS.expect(HEARTBEAT_SCHEMA, validate=True)
    def post(self):
        data = NS.payload
        try:
            timestamp = dateutil.parser.parse(data['timestamp'])
        except ValueError:
            abort(400, f"unable to parse timestamp: {data['timestamp']}")

        try:
            model.Device.update_from_heartbeat(
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
        """ get device(s) """
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
