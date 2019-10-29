from sqlalchemy import Column, String, Integer, Enum, \
    TIMESTAMP, func, JSON, ForeignKey, Boolean, Text, or_
from sqlalchemy.exc import SQLAlchemyError
from sqlalchemy.orm import relationship
import enum

from . import BASE, MA, SESSION
from . import LTMSDatabaseException
from src.utils.logging import get_module_logger
from .device_model import Device

LOGGER = get_module_logger()


class RecordingSession(BASE):
    """
    table storing active recording sessions
    """

    __tablename__ = "recording_session"

    # session ID
    id = Column(Integer, primary_key=True, autoincrement=True)

    # free form text notes
    notes = Column(Text)

    # recording session creation time
    creation_time = Column(
        TIMESTAMP(timezone=True),
        server_default=func.now(),
        nullable=False
    )

    # duration of recording session in seconds
    duration = Column(Integer, nullable=False)

    # user-specified portion of filenames
    file_prefix = Column(String, nullable=False)

    # should the device fragment the video files hourly?
    fragment_hourly = Column(Boolean)

    # extended attributes (for example, we may extend the option to specify a
    # target frames per second for the recording)
    extended_attributes = Column(JSON)

    # devices associated with this recording session
    devices = relationship("Device", backref="recording_session")
    device_statuses = relationship("DeviceRecordingStatus", backref="session", cascade="all, delete-orphan")

    @classmethod
    def get(cls):
        active_ids = SESSION.query(DeviceRecordingStatus.session_id).filter(or_(
            DeviceRecordingStatus.status == DeviceRecordingStatus.Status.RECORDING,
            DeviceRecordingStatus.status == DeviceRecordingStatus.Status.PENDING)).distinct(DeviceRecordingStatus.session_id)

        return SESSION.query(cls).filter(RecordingSession.id.in_(active_ids)).order_by(cls.creation_time.desc()).all()

    @classmethod
    def get_by_id(cls, session_id):
        return SESSION.query(cls).get(session_id)

    @staticmethod
    def create(device_ids, duration, file_prefix=None,
               fragment_hourly=False, notes=None,
               extended_attributes=None):

        new_session = RecordingSession(
            duration=duration,
            file_prefix=file_prefix,
            fragment_hourly=fragment_hourly,
            notes=notes,
            extended_attributes=extended_attributes
        )

        # select the devices and lock them for update to avoid race conditions
        # adding devices to multiple recording sessions at the same time
        devices = SESSION.query(Device).filter(Device.id.in_(device_ids)).with_for_update().all()

        for device in devices:
            if device.session_id is None:
                status = DeviceRecordingStatus(
                    device_id=device.id,
                    status=DeviceRecordingStatus.Status.PENDING
                )
                # only add the device to the session if it wasn't already
                # assigned to a session
                new_session.devices.append(device)
            else:
                # device already in use, don't make the relationship from the
                # session to the device, but we still record a failed status 
                status = DeviceRecordingStatus(
                    device_id=device.id,
                    status=DeviceRecordingStatus.Status.FAILED,
                    message=f"device {device.name} is already assigned to a recording session ({device.session_id})"
                )

            new_session.device_statuses.append(status)

        SESSION.add(new_session)
        try:
            SESSION.commit()
        except SQLAlchemyError:
            SESSION.rollback()
            raise LTMSDatabaseException("unable to commit new session")

        return new_session


class DeviceRecordingStatus(BASE):
    """
    table storing the status of each device participating in a recording session
    """
    __tablename__ = "session_device_status"

    class Status(enum.Enum):
        """
        device's status for the session
        """
        PENDING = enum.auto()    # device has yet to join recording session
        RECORDING = enum.auto()  # device has joined and is recording
        COMPLETE = enum.auto()   # device has recorded for specified duration
        FAILED = enum.auto()     # device encountered a failure during recording
        CANCELED = enum.auto()   # user manually stopped recording on device

    # device id and session id form a composite primary key
    device_id = Column(Integer, ForeignKey('device.id'), primary_key=True)
    session_id = Column(Integer, ForeignKey('recording_session.id', ondelete='CASCADE'), primary_key=True)

    # status of device for this session
    status = Column(Enum(Status), nullable=False)

    # how long (in seconds) the device has recorded as part of this session
    recording_time = Column(Integer, default=0)

    # message, if any, sent from device regarding current status
    # for example -- may contain an error message if status == FAILED
    message = Column(String)

    device = relationship("Device")

    def update_recording_time(self, duration):
        SESSION.begin_nested()
        self.recording_time = duration
        try:
            SESSION.commit()
        except SQLAlchemyError:
            SESSION.rollback()
            raise LTMSDatabaseException("unable to update recording_time")

    def update_status(self, new_status, message):
        self.status = new_status
        self.message = message
        try:
            SESSION.commit()
        except SQLAlchemyError:
            SESSION.rollback()
            raise LTMSDatabaseException("unable to update status")

    @classmethod
    def get_failed(cls):
        """
        get all devices with a FAILED state for this recording session
        :return: list of Device objects
        """
        failures = SESSION.query(cls).filter(
            cls.status == cls.Status.FAILED).all_or_none()
        return [f.device for f in failures]

    @classmethod
    def get_complete(cls):
        """
        get all devices with a COMPLETE state for this recording session
        :return: list of Device objects
        """
        completed = SESSION.query(cls).filter(
            cls.status == cls.Status.COMPLETE).all_or_none()
        return [c.device for c in completed]

    @classmethod
    def get_recording(cls):
        """
        get all devices with a RECORDING state for this recording session
        :return: list of Device objects
        """
        recording = SESSION.query(cls).filter(
            cls.status == cls.Status.RECORDING).all_or_none()
        return [r.device for r in recording]

    @classmethod
    def get_for_device(cls, device):
        return SESSION.query(cls).filter(cls.device_id == device.id,
                                         cls.session_id == device.session_id).one_or_none()


class RecordingSessionHistory(BASE):
    """
    table storing summaries of completed recording sessions
    """

    __tablename__ = "recording_session_history"

    # session ID
    id = Column(Integer, primary_key=True)

    # free form text notes
    notes = Column(Text)

    # recording session creation time
    creation_time = Column(
        TIMESTAMP(timezone=True),
        nullable=False
    )

    # recording session configuration
    configuration = Column(JSON)

    # summary of devices
    device_info = Column(JSON)

    @classmethod
    def get(cls, start_date=None, end_date=None):
        query = SESSION.query(cls)

        if start_date:
            query = query.filter(cls.creation_time >= start_date)

        if end_date:
            query = query.filter(cls.creation_time <= end_date)

        return query.all()
