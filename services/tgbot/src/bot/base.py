import logging
import queue
from typing import Callable

from src.access_control import AccessControlManager
from src.models import io as mio
from telegram.ext import ApplicationBuilder

from common import utils
from common.config import PathRegistry as PR

from .command_manager import CommandManager
from .task_manager import TaskManager


class BaseTelegramBot(CommandManager, TaskManager):

    PATH_TOKEN = PR.get_config_file("secrets/bot_api.txt")
    PATH_ADMIN = PR.get_config_file("secrets/admin_user.txt")
    _TASKS: dict[str, Callable] = {}

    logger = logging.getLogger("tgbot")

    def __init__(self, ac_manager: AccessControlManager):
        self.token = utils.read_text_file(self.PATH_TOKEN)
        self.app = ApplicationBuilder().token(self.token).build()
        CommandManager.__init__(self, self.app, ac_manager, self.logger)
        TaskManager.__init__(self, ac_manager, self.logger)
        self.admin_user = int(utils.read_text_file(self.PATH_ADMIN))

    def error_handler(self, update, context):
        # Log Errors caused by Updates or notify users of error, etc.
        print(f"Error occurred: {context.error}")

    async def task_send_message_admin(self, text: str) -> mio.TaskResponse:
        await self.app.bot.send_message(chat_id=self.admin_user, text=text)
        return mio.TaskResponse(message="Message sent")

    async def start(self):
        self.logger.info("starting telegram bot")
        await self.app.initialize()
        await self.app.start()
        await self.app.updater.start_polling()

    async def stop(self):
        self.logger.info("shutting down telegram bot")
        await self.app.updater.stop()
        await self.app.stop()
        await self.app.shutdown()

    async def run(self, message_queue: queue.Queue):
        # Add error handler
        self.app.add_error_handler(self.error_handler)
        # Handle async run
        # https://github.com/python-telegram-bot/python-telegram-bot/wiki/Frequently-requested-design-patterns#running-ptb-alongside-other-asyncio-frameworks
        await self.start()
        # Start other asyncio frameworks here
        await self.process_queue_messages(message_queue)
        # Add some logic that keeps the event loop running until you want to shutdown
        # Stop the other asyncio frameworks here
        await self.stop()
