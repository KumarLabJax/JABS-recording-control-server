#! /usr/bin/env python

import unittest
from datetime import datetime

from src.test import BaseDBTestCase
from src.utils.logging import get_module_logger

LOGGER = get_module_logger()


class TestHeartbeat(BaseDBTestCase):
    """ tests for the heartbeat endpoint """

    def test_heartbeat(self):
        """ test the heartbeat endpoint """
        payload = {
            'timestamp': datetime.utcnow().isoformat(),
            'name': "TEST-DEVICE",
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

        response = self.client.post('/api/device/heartbeat', json=payload)
        self.assertStatus(response, 204)

    def test_heartbeat_bad_state(self):
        """ test heartbeat endpoint with a bad device state """
        payload = {
            'timestamp': datetime.utcnow().isoformat(),
            'name': "TEST-DEVICE",
            'state': "BAD_STATE",
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
        response = self.client.post('/api/device/heartbeat', json=payload)
        self.assertStatus(response, 400)

    #TODO for completeness we should have test for all required fields
    def test_heartbeat_missing_required_field(self):
        """ test heartbeat endpoint missing a required field (name) """
        payload = {
            'timestamp': datetime.utcnow().isoformat(),
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
        response = self.client.post('/api/device/heartbeat', json=payload)
        self.assertStatus(response, 400)

    def test_heartbeat_bad_date_format(self):
        """
        test heartbeat endpoint with a bad datetime format (not ISO 8601)
        """
        payload = {
            'timestamp': datetime.utcnow().strftime('%A %B %d %Y bad 1234 format'),
            'name': "TEST_DEVICE",
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
        response = self.client.post('/api/device/heartbeat', json=payload)
        self.assertStatus(response, 400)


if __name__ == '__main__':
    unittest.main()
