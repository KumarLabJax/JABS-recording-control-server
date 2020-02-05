"""
The root of the API Blueprint code
"""

from flask_restplus import Api
from flask import Blueprint

from .utils.jwt import AUTHORIZATIONS


from .auth_controller import NS as auth_ns
from .device_controller import NS as device_ns
from .recording_session_controller import NS as rec_session_ns
from .user_controller import NS as user_ns


API_BLUEPRINT = Blueprint('api', __name__)
DESCRIPTION = (
    "Flask Service to coordinate the centralized control of multiple "
    "JAX Mouse Behavior Analysis enclosures"
)
API = Api(API_BLUEPRINT,
          title='JAX Mouse Behavior Analysis Control Service',
          version='0.0.1',
          description=DESCRIPTION,

          # Change this to 'Bearer Auth' to require token by default
          # we currently set it on a case by case basis
          security=None,
          authorizations=AUTHORIZATIONS,
          )


API.add_namespace(auth_ns)
API.add_namespace(device_ns)
API.add_namespace(rec_session_ns)
API.add_namespace(user_ns)

