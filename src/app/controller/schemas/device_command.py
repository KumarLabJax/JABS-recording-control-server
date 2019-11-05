from flask_restplus import fields, Model

__all__ = [
    'COMMAND_SCHEMA'
]

COMMAND_SCHEMA = Model('command', {
    'command_name': fields.String(
        required=True,
        description="command name"
    ),
    'parameters': fields.String(
        description="command parameters; JSON object specific to command type"
    )
})
