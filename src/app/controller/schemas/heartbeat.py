from flask_restplus import fields
from .device import DEVICE_BASE_SCHEMA

__all__ = ['HEARTBEAT_SCHEMA']

HEARTBEAT_SCHEMA = DEVICE_BASE_SCHEMA.clone('heartbeat', {
    'timestamp': fields.DateTime(
        required=True,
        description="iso8601 formatted datetime. UTC is assumed unless a timezone is specified"
    ),
    'session_id': fields.Integer(
        description="session ID of active recording session, null otherwise"
    ),
    'err_msg': fields.String(
        description="optional error message if the device was unable to process the last command"
    )
})
