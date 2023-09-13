from apscheduler.schedulers.background import BackgroundScheduler
from importlib import import_module
from django.conf import settings
from datetime import datetime

SCHEDULER = BackgroundScheduler()

# Get the full import path to the Command class
command_import_path = 'accounts.management.commands.refresh_hubstaff_tokens.Command'

# Import the Command class dynamically
module_name, class_name = command_import_path.rsplit('.', 1)
module = import_module(module_name)
CommandClass = getattr(module, class_name)

# Add the job using the Command class reference
SCHEDULER.add_job(CommandClass().handle, 'interval', hours=23,
                  minutes=59, next_run_time=datetime.now())  # set the next_run_time for the job and ensure it executes immediately when the server starts.

SCHEDULER.start()
