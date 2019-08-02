#! /usr/bin/env python

import unittest
from datetime import datetime

from src.test import BaseTestCase
from src.utils.logging import get_module_logger

LOGGER = get_module_logger()


class TestHeartbeat(BaseTestCase):

    def test_heartbeat(self):
        """
        test the heartbeat endpoint
        """
        payload = {
            'timestamp': datetime.utcnow().isoformat(),
            'name': "LEG-BH004",
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
        self.assert200(response)


if __name__ == '__main__':
    unittest.main()
