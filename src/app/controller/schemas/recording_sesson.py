from flask_restplus import fields, Model

__all__ = [
    'DEVICE_SESSION_STATUS',
    'RECORDING_SESSION_BASE_SCHEMA',
    'NEW_RECORDING_SESSION_SCHEMA',
    'RECORDING_SESSION_SCHEMA'
]

DEVICE_SESSION_STATUS = Model('device_session_status', {
    'device_id': fields.Integer(
        description="session ID"
    ),
    'device_name': fields.String(
        attribute=lambda s: s.device.name,
        description="device name"
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

RECORDING_SESSION_BASE_SCHEMA = Model('session_base', {
    'name': fields.String(
        required=True,
        description="recording session name"
    ),
    'notes': fields.String(
        description="free form text notes"
    ),
    'duration': fields.Integer(
        required=True,
        description="specified duration in seconds"
    ),
    'file_prefix': fields.String(
        description="user-specified filename prefix"
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
        'device_ids': fields.List(
            fields.Integer,
            description="IDs of devices to include in session",
            required=True
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
