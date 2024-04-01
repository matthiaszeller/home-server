import asyncio
import logging

from src.access_control import AccessControlManager
from src.exceptions import TaskNotFoundError, UnauthorizedAccessError
from src.models import io as mio


class TaskManager:
    def __init__(self, ac_manager: AccessControlManager, logger: logging.Logger):
        self.ac_manager = ac_manager
        self.logger = logger

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
