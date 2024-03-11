

import threading

from common.config import setup
setup(__file__)
from src.rest_api import run_flask_app
from src.bot import run_bot


if __name__ == '__main__':
    thread_rest_api = threading.Thread(target=run_flask_app)
    thread_rest_api.start()

    run_bot()

    thread_rest_api.join()
