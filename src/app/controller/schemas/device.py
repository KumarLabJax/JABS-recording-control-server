from flask_restplus import fields, Model

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
    'load_1min': fields.Float(
        required=True,
        description="1 minute load average"
    ),
    'load_5min': fields.Float(
        required=True,
        description="5 minute load average"
    ),
    'load_15min': fields.Float(
        required=True,
        description="15 minute load average"
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
    )
})

CAMERA_STATUS = Model('camera_status', {
    'recording': fields.Boolean(
        description="Boolean indicating if the device is recording video"
    ),
    'duration': fields.Integer(
        description="if the camera is recording, this value indicates the length of the recording session in seconds"
    ),
    'fps': fields.Integer(
        escription="If the camera is recording, this value indcates how many frames per second are being captured"
    )
})

SENSOR_STATUS = Model('sensor_status', {
    'camera': fields.Nested(CAMERA_STATUS)
})

DEVICE_BASE_SCHEMA = Model('device_base', {
    'name': fields.String(
        required=True,
        description="name of the device sending the heartbeat"
    ),
    'state': fields.String(enum=['IDLE', 'BUSY'], required=True,
                           description="Device State. BUSY (currently performing a task, e.g. recording) or IDLE"),
    'sensor_status': fields.Nested(SENSOR_STATUS, required=True,),
    'system_info': fields.Nested(SYSINFO_SCHEMA, required=True,)
})

DEVICE_SCHEMA = DEVICE_BASE_SCHEMA.clone('device', {
    'id': fields.Integer(required=True),
    'last_update': fields.DateTime(required=True),
    'system_info': fields.Nested(SYSINFO_SCHEMA, required=True,
                                 attribute=lambda d: {
                                     'uptime': d.uptime,
                                     'load_1min': d.load_1min,
                                     'load_5min': d.load_5min,
                                     'load_15min': d.load_15min,
                                     'total_ram': d.total_ram,
                                     'free_ram': d.free_ram,
                                     'free_disk': d.free_disk,
                                     'total_disk': d.total_disk
                                 })
})