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


class TelegramBot:

    PATH_TOKEN = PR.get_config_file("secrets/bot_api.txt")
    PATH_ADMIN = PR.get_config_file("secrets/admin_user.txt")
    _COMMANDS: dict[str, Callable] = {}

    def __init__(self):
        self.token = utils.read_text_file(self.PATH_TOKEN)
        self.app = ApplicationBuilder().token(self.token).build()
        self.admin_user = int(utils.read_text_file(self.PATH_ADMIN))

    @classmethod
    def __init_subclass__(cls, **kwargs):
        super().__init_subclass__(**kwargs)
        cls.__register_commands()

    @classmethod
    def __register_commands(cls):
        # get all methods from the class
        cls._COMMANDS = {
            name: method
            for name, method in dir(cls)
            if callable(method) and name.startswith("command_")
        }

    async def command_start(self, update, context: ContextTypes.DEFAULT_TYPE):
        await context.bot.send_message(
            chat_id=update.effective_chat.id, text="Hello! I'm your bot."
        )

    def error_handler(self, update, context):
        # Log Errors caused by Updates or notify users of error, etc.
        print(f"Error occurred: {context.error}")

    async def command_send_message(self, chat_id: int, text: str):
        await self.app.bot.send_message(chat_id=self.admin_user, text=text)

    async def process_queue_messages(self, message_queue: asyncio.Queue):
        logging.debug("starting processing message queue")
        while True:
            logging.info("waiting for queue msg")
            future: asyncio.Future
            command_message: dict
            command_message, future = await message_queue.get()
            logging.info("got queue msg")
            try:
                command = command_message["command"]
                data = command_message["data"]
                logging.debug(f"Got command from queue: {command}")

                # Handle the command
                command = self._COMMANDS.get(command)
                if command is None:
                    logging.error(f"Command not found: {command}")
                    future.set_exception(ValueError(f"Command not found: {command}"))
                    continue

                try:
                    result = await command(**data)
                    future.set_result({"status": "success", "result": result})
                except Exception as e:
                    logging.error(f"Error processing command: {e}")
                    future.set_exception(e)

            except Exception as e:
                logging.error(f"Error processing message: {e}")
            finally:
                message_queue.task_done()

    async def start(self):
        logging.info("starting telegram bot")
        await self.app.initialize()
        await self.app.start()
        await self.app.updater.start_polling()

    async def stop(self):
        logging.info("shutting down telegram bot")
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


async def run_bot(message_queue: asyncio.Queue):
    bot = TelegramBot()
    try:
        await bot.run(message_queue)
    except asyncio.CancelledError:
        await bot.stop()
