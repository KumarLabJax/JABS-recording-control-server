#! /usr/bin/env python

import unittest
import json
import dateutil

from datetime import datetime
import src.app.model as model

from src.test import BaseDBTestCase
from src.utils.logging import get_module_logger

LOGGER = get_module_logger()


class TestDevice(BaseDBTestCase):

    __endpoint = '/api/device'

    def setUp(self):

        sensor_status = {
            'camera': {
                'recording': False,
                'duration': 0,
                'fps': 0
            }
        }

        d1 = model.Device(
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

        d2 = model.Device(
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

        model.add_object(d1)
        model.add_object(d2)

    def test_device_list(self):
        """
        test the device endpoint
        """
        response = self.client.get(self.__endpoint)
        self.assert200(response)
        self.assertTrue(len(response.json) == 2)

    def test_device_list_by_state(self):
        """
        test the device endpoint filtering by state
        """
        response = self.client.get(self.__endpoint,
                                   query_string={'state': 'IDLE'})
        self.assert200(response)
        data = response.json
        self.assertTrue(len(data) == 1)
        self.assertEqual(data[0]['name'], "TEST-DEVICE1")

    def test_device_list_bad_state(self):
        """
        test the device endpoint filtering by state
        """
        response = self.client.get(self.__endpoint,
                                   query_string={'state': 'THIS_IS_BAD'})
        self.assert400(response)

    def test_device_by_id(self):
        """
        test endpoint to get device by ID
        """
        response = self.client.get(self.__endpoint + '/1')
        self.assert200(response)
        data = response.json
        self.assertEqual(data['id'], 1)
        self.assertEqual(data['name'], 'TEST-DEVICE1')

    def test_device_bad_id(self):
        """
        test endpoint to get device by ID, passing unknown ID
        """
        response = self.client.get(self.__endpoint + '/1234')
        self.assert404(response)


if __name__ == '__main__':
    unittest.main()
