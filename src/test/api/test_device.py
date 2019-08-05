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
        dev1 = {
            'timestamp': datetime.utcnow().isoformat(),
            'name': "TEST-DEVICE1",
            'state': "IDLE",
            'sensor_status': {
                'camera': {
                    'recording': False,
                    'duration': 0,
                    'fps': 0
                }
            },
            'system_info': {
                "uptime": 128324,
                "load_1min": 0.66,
                "load_5min": 0.23,
                "load_15min": 0.12,
                "total_ram": 8388608,
                "free_ram": 7759462,
                "free_disk": 1258291,
                "total_disk": 2000000
            }
        }

        dev2 = {
            'timestamp': datetime.utcnow().isoformat(),
            'name': "TEST-DEVICE2",
            'state': "BUSY",
            'sensor_status': {
                'camera': {
                    'recording': True,
                    'duration': 5765,
                    'fps': 29.8
                }
            },
            'system_info': {
                "uptime": 128995,
                "load_1min": 2.66,
                "load_5min": 2.23,
                "load_15min": 2.12,
                "total_ram": 8388608,
                "free_ram": 5759462,
                "free_disk": 1008291,
                "total_disk": 2000000
            }
        }

        model.Device.update_from_heartbeat(
            name=dev1['name'],
            state=model.Device.State[dev1['state']],
            last_update=dateutil.parser.parse(dev1['timestamp']),
            uptime=dev1['system_info']['uptime'],
            total_ram=dev1['system_info']['total_ram'],
            free_ram=dev1['system_info']['free_ram'],
            load_1min=dev1['system_info']['load_1min'],
            load_5min=dev1['system_info']['load_5min'],
            load_15min=dev1['system_info']['load_15min'],
            sensor_status=json.dumps(dev1['sensor_status']),
            total_disk=dev1['system_info']['total_disk'],
            free_disk=dev1['system_info']['free_disk']
        )

        model.Device.update_from_heartbeat(
            name=dev2['name'],
            state=model.Device.State[dev2['state']],
            last_update=dateutil.parser.parse(dev2['timestamp']),
            uptime=dev2['system_info']['uptime'],
            total_ram=dev2['system_info']['total_ram'],
            free_ram=dev2['system_info']['free_ram'],
            load_1min=dev2['system_info']['load_1min'],
            load_5min=dev2['system_info']['load_5min'],
            load_15min=dev2['system_info']['load_15min'],
            sensor_status=json.dumps(dev2['sensor_status']),
            total_disk=dev2['system_info']['total_disk'],
            free_disk=dev2['system_info']['free_disk']
        )

    def test_device_list(self):
        """
        test the device endpoint
        """
        response = self.client.get(self.__endpoint)
        self.assert200(response)
        data = response.json
        self.assertEqual(len(data), 2)

    def test_device_list_by_state(self):
        """
            test the device endpoint filtering by state
        """
        response = self.client.get(self.__endpoint,
                                   query_string={'state': 'IDLE'})
        self.assert200(response)
        data = response.json
        self.assertEqual(len(data), 1)
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
