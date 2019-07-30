"""
CLI Utilities
"""

import subprocess


def start_subprocess_and_wait(command_as_string):
    """
    Start a subprocess with Popen and wait for keyboard interrupt to kill it
    :param command_as_string: The command to launch
    :return:
    """

    process = subprocess.Popen(command_as_string.split(" "))
    try:
        process.wait()
    except KeyboardInterrupt:
        try:
            process.terminate()
        except OSError:
            pass
