import dateutil.parser
from flask_restplus import Resource, Namespace, reqparse, fields, abort
from .schemas import HEARTBEAT_SCHEMA, DEVICE_SCHEMA, SYSINFO_SCHEMA, SENSOR_STATUS, CAMERA_STATUS, add_models_to_namespace
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
                free_disk=data['system_info']['free_disk']
            )
        except LTMSControlServiceException as err:
            abort(400, f"error processing heartbeat {err}")

        return '', 204


@NS.route('/')
class Device(Resource):

    @NS.marshal_with(DEVICE_SCHEMA, as_list=True)
    def get(self):
        """
        get device(s)
        """
        return model.Device.all_devices()
