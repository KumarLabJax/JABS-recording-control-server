from flask_restplus import fields, Model
import json

__all__ = [
    'SYSINFO_SCHEMA',
    'CAMERA_STATUS',
    'SENSOR_STATUS',
    'DEVICE_SCHEMA',
    'DEVICE_BASE_SCHEMA'
]

SYSINFO_SCHEMA = Model('sysinfo', {
    'uptime': fields.Integer(
        required=True,
        description="system uptime in seconds"
    ),
    'load': fields.Float(
        required=True,
        description="1 minute load average"
    ),
    'total_ram': fields.Integer(
        required=True,
        description="total RAM in kilobytes"
    ),
    'free_ram': fields.Integer(
        required=True,
        description="free RAM in kilobytes"
    ),
    'free_disk': fields.Integer(
        required=True,
        description="free disk space in megabytes"
    ),
    'total_disk': fields.Integer(
        required=True,
        escription="total disk space in megabytes"
    ),
    'release': fields.String(
        required=True,
        description="release string provided by device client"
    )
})

CAMERA_STATUS = Model('camera_status', {
    'recording': fields.Boolean(
        description="Boolean indicating if the device is recording video",
        required=True
    ),
    'duration': fields.Integer(
        description=(
            "if the camera is recording, this value indicates the length of "
            "the recording session in seconds"
        )
    ),
    'fps': fields.Float(
        description=(
            "If the camera is recording, this value indcates how many frames "
            "per second are being captured"
        )
    )
})

SENSOR_STATUS = Model('sensor_status', {
    'camera': fields.Nested(CAMERA_STATUS, required=True)
})

DEVICE_BASE_SCHEMA = Model('device_base', {
    'name': fields.String(
        required=True,
        description="name of the device sending the heartbeat"
    ),
    'state': fields.String(
        enum=['IDLE', 'BUSY'], required=True, attribute=lambda d: d.state.name,
        description=("Device State. BUSY (currently performing a task, e.g. "
                     "recording) or IDLE"),
    ),
    'sensor_status': fields.Nested(SENSOR_STATUS, required=True,
                                   attribute=lambda d: json.loads(
                                       d.sensor_status)),
    'system_info': fields.Nested(SYSINFO_SCHEMA, required=True,
                                 attribute=lambda d: {
                                     'uptime': d.uptime,
                                     'load': d.load,
                                     'total_ram': d.total_ram,
                                     'free_ram': d.free_ram,
                                     'free_disk': d.free_disk,
                                     'total_disk': d.total_disk,
                                     'release': d.release
                                 })
})

DEVICE_SCHEMA = DEVICE_BASE_SCHEMA.clone('device', {
    'id': fields.Integer(required=True),
    'last_update': fields.DateTime(required=True),
})