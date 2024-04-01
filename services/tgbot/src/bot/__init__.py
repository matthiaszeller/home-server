import asyncio

from src.access_control import AccessControlManager

from .bot import TelegramBot


async def run_bot(message_queue: asyncio.Queue, ac_manager: AccessControlManager):
    bot = TelegramBot(ac_manager)
    try:
        await bot.run(message_queue)
    except asyncio.CancelledError:
        await bot.stop()
