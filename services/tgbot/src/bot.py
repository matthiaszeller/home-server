"""
https://github.com/python-telegram-bot/python-telegram-bot/wiki/Frequently-requested-design-patterns#running-ptb-alongside-other-asyncio-frameworks
"""


import asyncio
import logging
import queue

from telegram.ext import ApplicationBuilder, CommandHandler, ContextTypes

from common.config import PathRegistry as PR
from common import utils


class TelegramBot:

    PATH_TOKEN = PR.get_config_file('secrets/bot_api.txt')

    def __init__(self):
        self.token = utils.read_text_file(self.PATH_TOKEN)
        self.app = ApplicationBuilder().token(self.token).build()

    async def start(self, update, context: ContextTypes.DEFAULT_TYPE):
        await context.bot.send_message(chat_id=update.effective_chat.id, text="Hello! I'm your bot.")

    def error_handler(self, update, context):
        # Log Errors caused by Updates or notify users of error, etc.
        print(f"Error occurred: {context.error}")

    async def command_send_message(self, chat_id: int, text: str):
        await self.app.bot.send_message(chat_id=self.allowed_user, text=text)

    async def process_queue_messages(self, message_queue: asyncio.Queue):
        while True:
            command_message = await message_queue.get()
            try:
                command = command_message["command"]
                data = command_message["data"]
                logging.debug(f'Got command from queue: {command}')

                # Handle the command
                if command == "send_message":
                    await self.command_send_message(**data)
                # Add other command handling as necessary

            except Exception as e:
                logging.error(f'Error processing message: {e}')
            finally:
                message_queue.task_done()

    async def run(self, message_queue: queue.Queue):
        logging.info('starting telegram bot')
        # Add handlers
        start_handler = CommandHandler('start', self.start)
        self.app.add_handler(start_handler)

        # Add error handler
        self.app.add_error_handler(self.error_handler)

        # Handle async run
        # https://github.com/python-telegram-bot/python-telegram-bot/wiki/Frequently-requested-design-patterns#running-ptb-alongside-other-asyncio-frameworks

        logging.debug('starting the bot and polling')
        await self.app.initialize()
        await self.app.start()
        await self.app.updater.start_polling()
        # Start other asyncio frameworks here
        logging.debug('starting processing message queue')
        await self.process_queue_messages(message_queue)
        # Add some logic that keeps the event loop running until you want to shutdown
        # Stop the other asyncio frameworks here
        await self.app.updater.stop()
        await self.app.stop()
        await self.app.shutdown()


async def run_bot(message_queue: asyncio.Queue):
    try:
        bot = TelegramBot()
        await bot.run(message_queue)
    except Exception as e:
        logging.error(f'Unexpected error in run_bot: {e.__class__.__name__}: {e}')
        raise
