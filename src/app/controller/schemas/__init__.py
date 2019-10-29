from .heartbeat import *
from .device import *
from .recording_sesson import *
from .device_command import *


def add_models_to_namespace(namespace, models):
    for model in models:
        namespace.add_model(model.name, model)
    return namespace
