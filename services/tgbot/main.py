

import asyncio
import threading

from common.config import setup

setup(__file__)
from src.rest_api import run_flask_app
from src.bot import run_bot


if __name__ == '__main__':
    message_queue = asyncio.Queue()
    main_loop = asyncio.get_event_loop()

    thread_rest_api = threading.Thread(target=run_flask_app, args=(message_queue, main_loop))
    thread_rest_api.start()

    asyncio.run(run_bot(message_queue))

    thread_rest_api.join()
