#!/usr/bin/env python
from flask_script import Server, Manager

from api.app import create_app
from api import commands
from api.conf import Config

app = create_app(config_object=Config())
manager = Manager(app)

manager.add_command("runserver", Server())
manager.add_command('run_send_message_processor', commands.RunSendMessageProcessorCommand)
manager.add_command('run_callback_spreader', commands.RunCallbackSpreaderProcessorCommand)
manager.add_command('run_callback_delivery', commands.RunCallbackDeliveryProcessorCommand)

if __name__ == "__main__":
    manager.run()
