

import asyncio
import signal
import threading

from common.config import setup

setup(__file__)
from src.rest_api import run_flask_app
from src.bot import run_bot


message_queue = asyncio.Queue()


async def main():
    # Starting both the Flask (Quart) app and Telegram bot as tasks
    server_task = asyncio.create_task(run_flask_app(message_queue))
    bot_task = asyncio.create_task(run_bot(message_queue))

    # Wait for the tasks to finish (they won't unless cancelled)
    await asyncio.wait([server_task, bot_task], return_when=asyncio.FIRST_COMPLETED)


async def graceful_shutdown(signal, tasks):
    print(f"Received exit signal {signal.name}...")
    for task in tasks:
        task.cancel()
    print("Cancelled all tasks, exiting...")
    # Optionally, you can add more cleanup code here if needed


async def async_main():
    loop = asyncio.get_running_loop()

    # Prepare tasks for the main application logic
    tasks = asyncio.all_tasks(loop)
    # Exclude this main() task itself to prevent it from being cancelled prematurely
    tasks.remove(asyncio.current_task(loop))

    # Register signal handlers to ensure graceful shutdown
    for sig in (signal.SIGINT, signal.SIGTERM):
        loop.add_signal_handler(sig, lambda: asyncio.create_task(graceful_shutdown(sig, tasks)))

    await main()


if __name__ == '__main__':
    asyncio.run(async_main())
