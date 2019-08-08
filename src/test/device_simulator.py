#!/usr/bin/env python
"""
this script simulates a number of devices all sending heartbeat messages to
the server
"""

import argparse
from faker import Faker
import pytz
import random
import time
import requests
from urllib.parse import urljoin
import sys
from joblib import Parallel, delayed

faker = Faker()
random.seed()

MAX_JOBS = 8


class NameGenerator(object):
    count = 0

    def __init__(self, prefix):
        self.prefix = prefix

    def generate(self):
        self.count += 1
        return f"{self.prefix}-{self.count:02}"


class DeviceFaker(object):

    name_generator = NameGenerator("SIM")

    def __init__(self, server):
        self.server = server

    @classmethod
    def generate(cls):
        return {
            'name': cls.name_generator.generate(),
            'state': "IDLE",
            'sensor_status': {
                'camera': {
                    'recording': False,
                    'duration': 0,
                    'fps': 0
                }
            },
            'system_info': {
                "uptime": faker.random_int(min=4000, max=1000000),
                "total_ram": 8388608,
                "free_ram": 7759462,
                "free_disk": 1258291,
                "total_disk": 2000000
            }

        }

    def simulate_heartbeat(self, device, time_delta):
        """
        generate a fake heartbeat message using random data for the
        non-fixed values
        """
        device['timestamp'] = faker.date_time_between(start_date="now",
                                                      end_date="+5s",
                                                      tzinfo=pytz.utc).isoformat()

        sysinfo = device['system_info']

        sysinfo['load_1min'] = random.uniform(0, 4)
        sysinfo['load_5min'] = sysinfo['load_1min'] * random.uniform(0.8, 1.2)
        sysinfo['load_15min'] = sysinfo['load_5min'] * random.uniform(0.8, 1.2)
        sysinfo['uptime'] += time_delta
        sysinfo['free_ram'] = int(sysinfo['total_ram'] * random.uniform(0.2, 0.9))
        sysinfo['free_disk'] = int(sysinfo['total_disk'] * random.uniform(0.2, 0.9))

        endpoint = urljoin(self.server, 'api/device/heartbeat')
        result = requests.post(endpoint, json=device)
        if result.status_code != 204:
            print(f"WARNING: heartbeat returned {result.status_code}",
                  file=sys.stderr)


def main():

    parser = argparse.ArgumentParser()
    parser.add_argument('-n', '--num-devices', type=int, default=1,
                        help="number of devices to simulate")
    parser.add_argument('-t', '--time-delta', type=int, default=60,
                        help="number of seconds between heartbeat messages")
    parser.add_argument('--host', default="http://localhost:5000",
                        help="server hostname")

    args = parser.parse_args()

    devices = []
    device_faker = DeviceFaker(server=args.host)
    for i in range(1, args.num_devices+1):
        devices.append(device_faker.generate())

    with Parallel(n_jobs=MAX_JOBS) as parallel:
        while True:
            print(f"sending heartbeats from {len(devices)} devices")
            parallel(delayed(device_faker.simulate_heartbeat)(device, args.time_delta) for device in devices)
            print(f"sleeping {args.time_delta} seconds")
            time.sleep(args.time_delta)


if __name__ == '__main__':
    main()
