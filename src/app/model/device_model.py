import enum
import pytz
from sqlalchemy import Column, BigInteger, String, Integer, Float, Enum, \
    TIMESTAMP, func, JSON
from sqlalchemy.exc import SQLAlchemyError
from datetime import datetime, timedelta
import flask

from . import BASE, MA, SESSION
from .utils.unique import UniqueMixin
from . import LTMSDatabaseException
from src.utils.logging import get_module_logger

LOGGER = get_module_logger()


class Device(UniqueMixin, BASE):
    """ model representing a data acquisition device """
    __tablename__ = 'device'

    class State(enum.Enum):
        IDLE = enum.auto()
        BUSY = enum.auto()
        DOWN = enum.auto()

    id = Column(Integer, primary_key=True, autoincrement=True)
    name = Column(String, nullable=False, index=True, unique=True)

    # state of device (see State enum above for valid states)
    state = Column(Enum(State), nullable=False)

    # timestamp of last update message from this device
    last_update = Column(
        TIMESTAMP(timezone=True),
        server_default=func.now(),
        onupdate=func.current_timestamp(),
        nullable=False
    )

    # host information
    # system load
    load = Column(Float, default=0.0)

    # total physical memory in kilobytes
    total_ram = Column(BigInteger)

    # amount of free memory in kilobytes
    free_ram = Column(BigInteger)

    # system uptime in seconds
    uptime = Column(BigInteger)

    # free disk space in megabytes
    free_disk = Column(BigInteger)

    # total disk space in megabytes
    total_disk = Column(BigInteger)

    # JSON encoded sensor status
    sensor_status = Column(JSON)

    def state_to_str(self):
        """ Convert the status enum into a string """
        state_strings = {
            self.State.IDLE: "Idle",
            self.State.BUSY: "Busy",
            self.State.DOWN: "Down"
        }
        try:
            return state_strings[self.state]
        except KeyError:
            return "Unknown"

    @classmethod
    def unique_filter(cls, query, name):  # pylint: disable=W0222
        """
        used for the UniqueMixin, so we can select a device by name and
        automatically create a new one if it does not exist
        """
        return query.filter(Device.name == name)

    @staticmethod
    def __add_tz(dt):
        """
        adds a default timezone information to a naive datetime
        We assume timestamps passed in the heartbeat payload are UTC unless they
        specify otherwise, so if there is no tzinfo we'll set the timezone to
        UTC.

        the timestamp we get back from the database will have a timezone if
        we're using Postgresql. Postgres stores the time in UTC and by default
        will convert to the timezone in use by the connection.

        Dev/testing with SQLite will return the time in UTC with no tzinfo, so
        in that case we use this function as well to specify that the tz is
        UTC
        """
        if dt.tzinfo is None:
            return dt.replace(tzinfo=pytz.UTC)
        return dt

    @staticmethod
    def update_from_heartbeat(**kwargs):
        """
        this method is used to update a device from information sent in a
        "heartbeat" message
        """
        name = kwargs.pop('name')
        device = Device.as_unique(name=name)
        heartbeat_timestamp = Device.__add_tz(kwargs.pop('last_update'))

        if device.last_update is not None:
            last_update = Device.__add_tz(device.last_update)
            if last_update > heartbeat_timestamp:
                # TODO consider time skew?
                # do we want to check the timestamp contained in the hearbeat
                # with the last update timestamp in the database? otherwise we
                # should probably just get rid of the timestamp in the heartbeat
                # payload and just let the database update the last_update
                # column automatically
                LOGGER.warning(
                    "time skew detected: heartbeat has timestamp "
                    f"{heartbeat_timestamp.isoformat()} but last update was "
                    f"{last_update.isoformat()}"
                )

        device.last_update = heartbeat_timestamp
        for attr in kwargs:
            setattr(device, attr, kwargs[attr])
        try:
            SESSION.commit()
        except SQLAlchemyError:
            SESSION.rollback()
            raise LTMSDatabaseException(f"Unable to update device {name}")

    @classmethod
    def get_devices(cls, state=None):
        """ get list of devices, optionally filter by device state """
        cls.check_for_down_devices()
        query = SESSION.query(cls)
        if state is not None:
            query = query.filter(cls.state == state)
        return query.order_by(cls.name).all()

    @classmethod
    def get_by_id(cls, device_id):
        """ get a device by its ID """
        cls.check_for_down_devices()
        return SESSION.query(cls).get(device_id)

    @classmethod
    def get_by_name(cls, name):
        """ get a device by its name """
        cls.check_for_down_devices()
        return SESSION.query(cls).filter(cls.name == name).one_or_none()

    @classmethod
    def check_for_down_devices(cls):
        """
        check for devices that we haven't heard from in a while and set their
        state to down
        """
        since = cls.__add_tz(datetime.utcnow() - timedelta(seconds=flask.current_app.config['DOWN_DEVICE_THRESHOLD']))
        SESSION.query(cls).filter(cls.last_update < since).update({'state': cls.State.DOWN, 'last_update': cls.last_update})
        try:
            SESSION.commit()
        except SQLAlchemyError:
            SESSION.rollback()


class DeviceSchema(MA.ModelSchema):
    """Creates a serializer from the sqlalchemy model definition"""
    class Meta:
        """Metaclass"""
        model = Device
        strict = True
