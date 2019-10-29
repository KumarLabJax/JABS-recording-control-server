from flask_restplus import fields, Model

__all__ = [
    'COMMAND_SCHEMA',
    'HEARTBEAT_REPLY_SCHEMA'
]

COMMAND_SCHEMA = Model('command', {
    'command': fields.String(
        required=True,
        description="command name"
    ),
    'parameters': fields.String(
        description="command parameters; JSON object specific to command type"
    )
})

HEARTBEAT_REPLY_SCHEMA = Model('heartbeat_reply', {
    'commands': fields.List(
        fields.Nested(COMMAND_SCHEMA),
        description="commands for device"
    )
})