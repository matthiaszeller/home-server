"""
https://github.com/python-telegram-bot/python-telegram-bot/wiki/Frequently-requested-design-patterns#running-ptb-alongside-other-asyncio-frameworks
"""

import asyncio
import logging
import queue
from typing import Callable

from telegram.ext import ApplicationBuilder, CommandHandler, ContextTypes

from common import utils
from common.config import PathRegistry as PR

from .access_control import AccessControlManager
from .exceptions import TaskNotFoundError, UnauthorizedAccessError
from .models import io as mio


class BaseTelegramBot:

    PATH_TOKEN = PR.get_config_file("secrets/bot_api.txt")
    PATH_ADMIN = PR.get_config_file("secrets/admin_user.txt")
    _TASKS: dict[str, Callable] = {}

    logger = logging.getLogger("tgbot")

    def __init__(self, ac_manager: AccessControlManager):
        self.token = utils.read_text_file(self.PATH_TOKEN)
        self.app = ApplicationBuilder().token(self.token).build()
        self.admin_user = int(utils.read_text_file(self.PATH_ADMIN))
        self.ac_manager = ac_manager

    @classmethod
    def __init_subclass__(cls, **kwargs):
        super().__init_subclass__(**kwargs)
        cls.__register_tasks()

    @classmethod
    def __register_tasks(cls):
        """Register all task methods from the subclass."""

        def process_task_name(name):
            return name.replace("task_", "")

        # get all methods from the class
        cls._TASKS = {
            process_task_name(name): getattr(cls, name)
            for name in dir(cls)
            if name.startswith("task_")
        }
        cls.logger.info(f"Registered tasks: {', '.join(cls._TASKS.keys())}")

    async def command_start(self, update, context: ContextTypes.DEFAULT_TYPE):
        await context.bot.send_message(
            chat_id=update.effective_chat.id, text="Hello! I'm your bot."
        )

    def error_handler(self, update, context):
        # Log Errors caused by Updates or notify users of error, etc.
        print(f"Error occurred: {context.error}")

    async def task_send_message_admin(self, text: str) -> mio.TaskResponse:
        await self.app.bot.send_message(chat_id=self.admin_user, text=text)
        return mio.TaskResponse(message="Message sent")

    async def process_queue_messages(self, message_queue: asyncio.Queue):
        """Processes messages from the queue and executes tasks with authorization checks."""
        self.logger.debug("starting processing message queue")
        while True:
            self.logger.debug("waiting for queue msg")
            future: asyncio.Future
            task_message: mio.MessageInQueue
            task_message, future = await message_queue.get()
            self.logger.info("got queue msg")

            try:
                task_data = task_message.task

                if not self._authorize_task(task_message):
                    self._reject_unauthorized_task(future, task_data.task)
                    continue

                await self._execute_task(task_data, future)

            except Exception as e:
                self.logger.error(f"Error processing message: {e}")
            finally:
                message_queue.task_done()

    def _authorize_task(self, task_message: mio.MessageInQueue) -> bool:
        """Checks if the service is authorized to perform the requested task."""
        token = task_message.api_token
        task = task_message.task.task
        self.logger.info(f"Checking authorization for task: {task}")
        return self.ac_manager.check_api_access(token, task)

    def _reject_unauthorized_task(self, future: asyncio.Future, task: str):
        """Sets an exception on the future for unauthorized tasks."""
        self.logger.warning(f"Unauthorized access attempt for task: {task}")
        future.set_exception(
            UnauthorizedAccessError(f"Unauthorized access for task: {task}")
        )

    async def _execute_task(self, task_data: mio.TgbotTask, future: asyncio.Future):
        """Executes the task and sets the result or exception on the future."""
        try:
            task = self._TASKS.get(task_data.task)
            if task is None:
                raise TaskNotFoundError(f"Task not found: {task_data.task}")

            task_response: mio.TaskResponse = await task(self, **task_data.args)
            future.set_result(task_response)
        except Exception as e:
            self.logger.error(f"Error processing task: {e}")
            future.set_exception(e)

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
        # Add handlers
        start_handler = CommandHandler("start", self.start)
        self.app.add_handler(start_handler)

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


class TelegramBot(BaseTelegramBot):
    pass


async def run_bot(message_queue: asyncio.Queue, ac_manager: AccessControlManager):
    bot = TelegramBot(ac_manager)
    try:
        await bot.run(message_queue)
    except asyncio.CancelledError:
        await bot.stop()
