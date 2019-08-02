"""
The root of the API Blueprint code
"""

from flask_restplus import Api
from flask import Blueprint

from .utils.jwt import AUTHORIZATIONS


from .auth_controller import NS as auth_ns
from .device_controller import NS as device_ns


API_BLUEPRINT = Blueprint('api', __name__)
DESCRIPTION = 'Flask Service to coordinate the centralized control of multiple long-term monitoring systems'
API = Api(API_BLUEPRINT,
          title='Long-Term Monitoring System Control Service',
          version='0.0.1',
          description=DESCRIPTION,

          # Change this to 'Bearer Auth' to require token by default
          security=None,
          authorizations=AUTHORIZATIONS,

          )


API.add_namespace(auth_ns)
API.add_namespace(device_ns)
