"""
Tests related to database availability, creation, and interaction
"""

# This next line disables checking that instance of 'scoped_session'
# has no 'commit' or 'bulk_save_objects' members, The members are there,
# pylint just can't tell
#pylint: disable=E1101

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
            load_1min=0.66,
            load_5min=0.23,
            load_15min=0.12,
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
            load_1min=0.66,
            load_5min=0.23,
            load_15min=0.12,
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

    def test_query_nonexistant_device(self):
        """ Test that getting by non-existant name has no result """
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


if __name__ == '__main__':
    unittest.main()
