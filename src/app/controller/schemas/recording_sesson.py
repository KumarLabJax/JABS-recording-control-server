from flask_restplus import fields, Model

__all__ = [
    'DEVICE_SESSION_STATUS',
    'RECORDING_SESSION_BASE_SCHEMA',
    'NEW_RECORDING_SESSION_SCHEMA',
    'RECORDING_SESSION_SCHEMA',
    'DEVICE_SPECIFICATION_SCHEMA'
]

DEVICE_SESSION_STATUS = Model('device_session_status', {
    'device_id': fields.Integer(
        description="device ID"
    ),
    'device_name': fields.String(
        attribute=lambda s: s.device.name,
        description="device name"
    ),
    'filename_prefix': fields.String(
        description="filename prefix"
    ),
    'recording_time': fields.Integer(
        description="how long (in seconds) the device has recorded as part of this session"
    ),
    'status': fields.String(
        attribute=lambda s: s.status.name,
        description="Status as a string (e.g. 'RECORDING', 'FAILED', 'COMPLETE', ...)"
    ),
    'message': fields.String(
        description="additional status information. always set for FAILED."
    )
})

DEVICE_SPECIFICATION_SCHEMA = Model('device_spec', {
    'device_id': fields.Integer(
        required=True,
        description="device id"
    ),
    'filename_prefix': fields.String(
        required=True,
        description="filename prefix"
    )
})

RECORDING_SESSION_BASE_SCHEMA = Model('session_base', {
    'name': fields.String(
        required=True,
        description="recording session name"
    ),
    'duration': fields.Integer(
        required=True,
        description="specified duration in seconds"
    ),
    'fragment_hourly': fields.Boolean(
        description="fragment video files hourly",
        required=True
    ),
    'target_fps': fields.Integer(
        description="target frames per second",
        required=True
    ),
    'apply_filter': fields.Boolean(
        description="enable filtering during video encoding",
        required=True
    )
})

NEW_RECORDING_SESSION_SCHEMA = RECORDING_SESSION_BASE_SCHEMA.clone(
    'new_session', {
        'device_spec': fields.List(
            fields.Nested(DEVICE_SPECIFICATION_SCHEMA),
            description="recording session devices and any device specific information"
        )
    }
)

RECORDING_SESSION_SCHEMA = RECORDING_SESSION_BASE_SCHEMA.clone('active_session', {
    'id': fields.Integer(
        description="session ID"
    ),
    'creation_time': fields.DateTime(
        description="iso8601 formatted datetime"
    ),
    'device_statuses': fields.List(
        fields.Nested(DEVICE_SESSION_STATUS),
        description="status of devices assigned to recording session"
    ),
    'status': fields.String(
        attribute=lambda s: s.status.name,
        description="session status"
    )
})
