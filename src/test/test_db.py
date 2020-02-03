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
            last_update=datetime.utcnow(),
            uptime=128324,
            total_ram=8388608,
            free_ram=7759462,
            load=0.66,
            sensor_status=json.dumps(sensor_status),
            total_disk=2000000,
            free_disk=1258291
        )

        device3 = model.Device(
            name="TEST-DEVICE3",
            release="fake device",
            last_update=datetime.utcnow(),
            uptime=128324,
            total_ram=8388608,
            free_ram=7759462,
            load=0.66,
            sensor_status=json.dumps(sensor_status),
            total_disk=2000000,
            free_disk=1258291
        )

        self.session.bulk_save_objects([device1, device2, device3])
        self.session.commit()

    def tearDown(self):
        self.session.query(model.Device).delete()
        self.session.query(model.DeviceRecordingStatus).delete()
        self.session.query(model.RecordingSession).delete()
        self.session.commit()
        self.session.remove()

    def test_new_session(self):
        """Test creating new recording session"""
        device1 = model.Device.get_by_name("TEST-DEVICE1")

        device_spec = [
            {
                'device_id': device1.id,
                'filename_prefix': "test_prefix"
            }
        ]

        new_session = model.RecordingSession.create(device_spec, duration=600,
                                                    name="test session",
                                                    fragment_hourly=True,
                                                    target_fps=30,
                                                    apply_filter=True)

        self.assertTrue(len(new_session.device_statuses) == 1)
        self.assertEqual(new_session.duration, 600)
        self.assertTrue(new_session.fragment_hourly)
        self.assertEqual(new_session.target_fps, 30)
        self.assertEqual(new_session.name, "test session")

    def test_change_device_status(self):
        """Test changing device's status from PENDING to RECORDING"""
        device2 = model.Device.get_by_name("TEST-DEVICE2")

        device_spec = [
            {
                'device_id': device2.id,
                'filename_prefix': "test_prefix"
            }
        ]

        new_session = model.RecordingSession.create(device_spec, duration=600,
                                                    name="test session 2",
                                                    fragment_hourly=True,
                                                    target_fps=30,
                                                    apply_filter=True)

        self.assertEqual(new_session.device_statuses[0].status,
                         model.DeviceRecordingStatus.Status.PENDING)

        new_session.device_statuses[0].status = model.DeviceRecordingStatus.Status.RECORDING

        self.session.commit()

        self.assertEqual(new_session.device_statuses[0].status,
                         model.DeviceRecordingStatus.Status.RECORDING)

    def test_session_device_order(self):
        """Test recording session device status sorting"""
        device1 = model.Device.get_by_name("TEST-DEVICE1")
        device2 = model.Device.get_by_name("TEST-DEVICE2")
        device3 = model.Device.get_by_name("TEST-DEVICE3")

        device_spec = [
            {
                'device_id': device2.id,
                'filename_prefix': "test_prefix2"
            },
            {
                'device_id': device1.id,
                'filename_prefix': "test_prefix"
            },
            {
                'device_id': device3.id,
                'filename_prefix': "test_prefix3"
            }
        ]

        new_session = model.RecordingSession.create(device_spec, duration=600,
                                                    name="test session",
                                                    fragment_hourly=True,
                                                    target_fps=30,
                                                    apply_filter=True)

        # devices should be sorted by name in device_statusess
        self.assertEqual(new_session.device_statuses[0].device_name,
                         "TEST-DEVICE1")
        self.assertEqual(new_session.device_statuses[1].device_name,
                         "TEST-DEVICE2")
        self.assertEqual(new_session.device_statuses[2].device_name,
                         "TEST-DEVICE3")


if __name__ == '__main__':
    unittest.main()
