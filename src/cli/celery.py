"""
Starts the dev server
"""

from flask_script import Command, Option
from .utils import start_subprocess_and_wait

class StartCeleryWorkersCommand(Command):
    """
    Start the celery worker(s)
    """

    option_list = (
        Option('--num', '-n', dest='number', default=1, type=int,
               help="Worker Concurrency"),
        Option('--logfile', '-f', dest='logfile', required=False,
               help="Location of logfile, stderr if none"),
    )

    def run(self, number, logfile=None):  # pylint: disable=E0202,W0221
        """ invoked by the command """
        # TODO: This cmd needs to reference the task module/namespace
        celery_cmdline = 'celery worker -A src.app.service.task_service_example -l INFO'
        if number > 1:
            celery_cmdline = celery_cmdline + f" --concurrency={number}"
        if logfile:
            celery_cmdline += f" --logfile={logfile}"
        start_subprocess_and_wait(celery_cmdline)
