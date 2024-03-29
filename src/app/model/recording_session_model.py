from sqlalchemy import Column, String, Integer, Enum, \
    TIMESTAMP, func, ForeignKey, Boolean, select
from sqlalchemy.exc import SQLAlchemyError
from sqlalchemy.orm import relationship, deferred
import enum

from . import BASE, MA, SESSION
from . import JaxMBADatabaseException
from src.utils.logging import get_module_logger
from .device_model import Device

LOGGER = get_module_logger()


class RecordingSession(BASE):
    """
    table storing active recording sessions
    """

    class Status(enum.Enum):
        """
        device's status for the session
        """
        IN_PROGRESS = enum.auto()  # recording session is in progress
        COMPLETE = enum.auto()     # session is complete
        CANCELED = enum.auto()     # user canceled session

    __tablename__ = "recording_session"

    # session ID
    id = Column(Integer, primary_key=True, autoincrement=True)

    name = Column(String, nullable=False)

    # status of device for this session
    status = Column(Enum(Status, name="session_state"), nullable=False, default=Status.IN_PROGRESS)

    # recording session creation time
    creation_time = Column(
        TIMESTAMP(timezone=True),
        server_default=func.now(),
        nullable=False
    )

    archived = Column(Boolean, nullable=False, default=False)

    # duration of recording session in seconds
    duration = Column(Integer, nullable=False)

    # user-specified portion of filenames
    file_prefix = Column(String, nullable=True)

    # should the device fragment the video files hourly?
    fragment_hourly = Column(Boolean, nullable=False)

    # pass frames through filter graph before writing to file?
    apply_filter = Column(Boolean, nullable=False)

    # target frame capture rate
    target_fps = Column(Integer, nullable=False)

    # devices associated with this recording session
    devices = relationship("Device", backref="recording_session")
    device_statuses = relationship("DeviceRecordingStatus",
                                   back_populates="session",
                                   cascade="all, delete, delete-orphan",
                                   order_by="DeviceRecordingStatus.device_name")

    def archive(self):
        self.archived = True

        try:
            SESSION.commit()
        except SQLAlchemyError:
            SESSION.rollback()
            raise JaxMBADatabaseException("unable to archive recording session")

    def cancel(self):
        for ds in self.device_statuses:
            if ds.status == DeviceRecordingStatus.Status.PENDING or ds.status == DeviceRecordingStatus.Status.RECORDING:
                ds.status = DeviceRecordingStatus.Status.CANCELED
        self.status = self.Status.CANCELED
        try:
            SESSION.commit()
        except SQLAlchemyError:
            SESSION.rollback()
            raise JaxMBADatabaseException("unable to cancel recording session")

    def update_status(self):
        if self.status == self.Status.IN_PROGRESS:
            for ds in self.device_statuses:
                if ds.status in [DeviceRecordingStatus.Status.RECORDING, DeviceRecordingStatus.Status.PENDING]:
                    # still in progress
                    return
            self.status = self.Status.COMPLETE
            try:
                SESSION.commit()
            except SQLAlchemyError:
                SESSION.rollback()
                raise JaxMBADatabaseException(
                    "unable to cancel recording session")

    @classmethod
    def get(cls):
        return SESSION.query(cls).filter(cls.archived == False).order_by(cls.creation_time.desc()).all()

    @classmethod
    def get_archived(cls):
        return SESSION.query(cls).filter(cls.archived).order_by(
            cls.creation_time.desc()).all()

    @classmethod
    def get_by_id(cls, session_id):
        return SESSION.query(cls).get(session_id)

    @staticmethod
    def create(device_spec, duration, name, fragment_hourly, target_fps,
               apply_filter):

        new_session = RecordingSession(
            duration=duration,
            fragment_hourly=fragment_hourly,
            target_fps=target_fps,
            apply_filter=apply_filter,
            name=name
        )

        # select the devices and lock them for update to avoid race conditions
        # adding devices to multiple recording sessions at the same time
        device_ids = [d['device_id'] for d in device_spec]
        file_prefixes = {}
        for spec in device_spec:
            file_prefixes[spec['device_id']] = spec['filename_prefix']
        devices = SESSION.query(Device).filter(Device.id.in_(device_ids)).with_for_update().all()

        for device in devices:
            if device.session_id is None:
                status = DeviceRecordingStatus(
                    device_id=device.id,
                    file_prefix=file_prefixes[device.id],
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
            raise JaxMBADatabaseException("unable to commit new session")

        return new_session

    @classmethod
    def check_for_complete(cls):
        """
        check for sessions that should have their state changed to complete
        """

        sessions = SESSION.query(cls).filter(cls.status == cls.Status.IN_PROGRESS)
        for s in sessions:
            s.update_status()


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
    session_id = Column(Integer,
                        ForeignKey('recording_session.id', ondelete='CASCADE'),
                        primary_key=True)

    # device's file prefix for this recording session
    file_prefix = Column(String)

    # status of device for this session
    status = Column(Enum(Status, name="device_session_state"), nullable=False)

    # how long (in seconds) the device has recorded as part of this session
    recording_time = Column(Integer, default=0)

    # message, if any, sent from device regarding current status
    # for example -- may contain an error message if status == FAILED
    message = Column(String)

    device = relationship("Device")
    session = relationship("RecordingSession",
                           back_populates="device_statuses")

    # so the RecordingSession can sort DeviceRecordingSessionStatus by name
    device_name = deferred(select([Device.name]).where(Device.id == device_id))

    def update_recording_time(self, duration):
        self.recording_time = duration
        try:
            SESSION.commit()
        except SQLAlchemyError:
            SESSION.rollback()
            raise JaxMBADatabaseException("unable to update recording_time")

    def update_status(self, new_status, message=None):
        self.status = new_status
        self.message = message
        try:
            SESSION.commit()
        except SQLAlchemyError:
            SESSION.rollback()
            raise JaxMBADatabaseException("unable to update status")

    def remove_from_session(self):
        if self.status == self.Status.RECORDING or self.status == self.Status.PENDING:
            self.update_status(self.Status.CANCELED)

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
    def get(cls, device, session):
        return SESSION.query(cls).filter(cls.device_id == device.id,
                                         cls.session_id == session.id).one_or_none()
