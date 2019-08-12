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
    """
    this class is used to generate device names based on a prefix and an
    incrementing sequential number
    """

    count = 0

    def __init__(self, prefix):
        self.prefix = prefix

    def generate(self):
        """ return a new device name """
        self.count += 1
        return f"{self.prefix}-{self.count:02}"


class DeviceFaker(object):
    """ this class is used to generate fake devices """

    name_generator = NameGenerator("SIM")

    def __init__(self, server):
        self.server = server

    @classmethod
    def generate(cls):
        """
        returns a dictionary that describes a faked device. some attributes are
        not set by this method, but they will be set/updated each time that
        simulate_heartbeat is called
        """
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
                "uptime": random.randint(4000, 1000000),
                "total_ram": 8388608,
                "total_disk": 2000000
            }

        }

    def simulate_heartbeat(self, device, time_delta):
        """
        generate a fake heartbeat message using random data for the
        non-fixed values
        """

        # add a little jitter into the time stamp for this heartbeat message so
        # we have some variation in the timestamp
        timestamp = faker.date_time_between(start_date="-5s",
                                            end_date="now",
                                            tzinfo=pytz.utc)
        device['timestamp'] = timestamp.isoformat()

        sysinfo = device['system_info']

        # generate a random floating point number for the load
        sysinfo['load'] = random.uniform(0, 4)

        # increment the uptime by the time_delta to get the new uptime
        sysinfo['uptime'] += time_delta

        # free ram and free disk are generated by multiplying the total by a
        # random scailing factor
        sysinfo['free_ram'] = int(
            sysinfo['total_ram'] * random.uniform(0.2, 0.9))
        sysinfo['free_disk'] = int(
            sysinfo['total_disk'] * random.uniform(0.2, 0.9))

        # now that we have all the values we need for the heartbeat endpoint
        # payload, we send the request
        endpoint = urljoin(self.server, 'api/device/heartbeat')
        result = requests.post(endpoint, json=device)

        # result processing will need to be modified once the backend responds
        # with commands for the clients
        if result.status_code != 204:
            print(f"WARNING: heartbeat returned {result.status_code}",
                  file=sys.stderr)


def main():

    parser = argparse.ArgumentParser()
    parser.add_argument('-n', '--num-devices', type=int, default=1,
                        help="number of devices to simulate")
    parser.add_argument('-t', '--time-delta', type=int, default=10,
                        help="number of seconds between heartbeat messages")
    parser.add_argument('--host', default="http://localhost:5000",
                        help="server hostname")

    args = parser.parse_args()

    devices = []
    device_faker = DeviceFaker(server=args.host)
    while len(devices) < args.num_devices:
        devices.append(device_faker.generate())

    # send some of the heartbeat messages in parallel
    with Parallel(n_jobs=MAX_JOBS) as parallel:
        while True:
            print(f"sending heartbeats from {len(devices)} devices")

            parallel(
                delayed(device_faker.simulate_heartbeat)(device,
                                                         args.time_delta)
                for device in devices
            )
            print(f"sleeping {args.time_delta} seconds")
            time.sleep(args.time_delta)


if __name__ == '__main__':
    main()
