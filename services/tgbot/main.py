import asyncio
import signal

from common.config import PathRegistry as PR
from common.config import setup

setup(__file__)
from src.access_control import AccessControlManager  # noqa E402
from src.bot import run_bot  # noqa E402
from src.rest_api import run_fastapi_app  # noqa E402

message_queue = asyncio.Queue()
ac_manager = AccessControlManager(
    path_permissions=PR.get_config_file("permissions.yaml"),
    path_dotenv=PR.PATH_ROOT / ".env",
)


async def main():
    # Starting both the FastAPI app and Telegram bot as tasks
    server_task = asyncio.create_task(run_fastapi_app(message_queue, ac_manager))
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
        loop.add_signal_handler(
            sig, lambda: asyncio.create_task(graceful_shutdown(sig, tasks))  # noqa B023
        )

    await main()


if __name__ == "__main__":
    asyncio.run(async_main())
