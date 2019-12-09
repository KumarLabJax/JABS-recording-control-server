"""
Tests related to database availability, creation, and interaction
"""

# This next line disables checking that instance of 'scoped_session'
# has no 'commit' or 'bulk_save_objects' members, The members are there,
# pylint just can't tell
# pylint: disable=E1101

import unittest
from datetime import datetime
import json

from src.test import BaseDBTestCase
from src.app import model


class DbConnectionTest(BaseDBTestCase):
    """ Is the database available ? """

    def test_db(self):
        """ Smoke test """
        with self.engine.connect() as conn:
            self.assertFalse(conn.closed)


class SqlalchemyDeviceModelTest(BaseDBTestCase):
    """ Test interacting with the provided sqlalchemy definitions """

    def setUp(self):

        sensor_status = {
            'camera': {
                'recording': False,
                'duration': 0,
                'fps': 0
            }
        }

        device1 = model.Device(
            name="TEST-DEVICE1",
            state=model.Device.State.IDLE,
            last_update=datetime.utcnow(),
            uptime=128324,
            total_ram=8388608,
            free_ram=7759462,
            load=0.66,
            sensor_status=json.dumps(sensor_status),
            total_disk=2000000,
            free_disk=1258291
        )

        sensor_status = {
            'camera': {
                'recording': True,
                'duration': 5765,
                'fps': 29.8
            }
        }

        device2 = model.Device(
            name="TEST-DEVICE2",
            state=model.Device.State.BUSY,
            last_update=datetime.utcnow(),
            uptime=128324,
            total_ram=8388608,
            free_ram=7759462,
            load=0.66,
            sensor_status=json.dumps(sensor_status),
            total_disk=2000000,
            free_disk=1258291
        )

        self.session.bulk_save_objects([device1, device2])
        self.session.commit()

    def test_get_devices(self):
        """ Test getting back all entries """
        devices = model.Device.get_devices()
        self.assertTrue(len(devices) == 2)

    def test_get_by_name(self):
        """ Test getting device by name """
        device = model.Device.get_by_name("TEST-DEVICE2")
        self.assertIsNotNone(device)

    def test_query_nonexistant_device(self):
        """ Test that getting by non-existant id has no result """
        device = model.Device.get_by_id(1234)
        self.assertEqual(device, None)

    def test_delete_model(self):
        """ Test that the entry can be deleted """
        self.session.query(model.Device).delete()
        self.session.commit()
        devices = model.Device.get_devices()
        self.assertEqual(len(devices), 0)

    def tearDown(self):
        self.session.query(model.Device).delete()
        self.session.commit()
        self.session.remove()


class SqlalchemyRecordingSessionModelTest(BaseDBTestCase):
    def setUp(self):
        sensor_status = {
            'camera': {
                'recording': False,
                'duration': 0,
                'fps': 0
            }
        }

        device1 = model.Device(
            name="TEST-DEVICE1",
            release="fake device",
            state=model.Device.State.IDLE,
            last_update=datetime.utcnow(),
            uptime=128324,
            total_ram=8388608,
            free_ram=7759462,
            load=0.66,
            sensor_status=json.dumps(sensor_status),
            total_disk=2000000,
            free_disk=1258291
        )

        device2 = model.Device(
            name="TEST-DEVICE2",
            release="fake device",
            state=model.Device.State.IDLE,
            last_update=datetime.utcnow(),
            uptime=128324,
            total_ram=8388608,
            free_ram=7759462,
            load=0.66,
            sensor_status=json.dumps(sensor_status),
            total_disk=2000000,
            free_disk=1258291
        )

        self.session.bulk_save_objects([device1, device2])
        self.session.commit()

    def tearDown(self):
        self.session.query(model.Device).delete()
        self.session.query(model.DeviceRecordingStatus).delete()
        self.session.query(model.RecordingSession).delete()
        self.session.commit()
        self.session.remove()

    def test_new_session(self):

        device1 = model.Device.get_by_name("TEST-DEVICE1")

        new_session = model.RecordingSession.create([device1], duration=600,
                                                    file_prefix="test_prefix",
                                                    fragment_hourly=True)

        self.assertTrue(len(new_session.device_statuses) == 1)
        self.assertEqual(new_session.duration, 600)
        self.assertTrue(new_session.fragment_hourly)

    def test_change_device_status(self):
        device2 = model.Device.get_by_name("TEST-DEVICE2")

        new_session = model.RecordingSession.create([device2], duration=600,
                                                    file_prefix="test_prefix",
                                                    fragment_hourly=True)

        self.assertEqual(new_session.device_statuses[0].status,
                         model.DeviceRecordingStatus.Status.PENDING)

        new_session.device_statuses[0].status = model.DeviceRecordingStatus.Status.RECORDING

        self.assertEqual(new_session.device_statuses[0].status,
                         model.DeviceRecordingStatus.Status.RECORDING)


if __name__ == '__main__':
    unittest.main()
