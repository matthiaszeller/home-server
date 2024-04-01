import logging
from functools import wraps

from src.access_control import AccessControlManager
from telegram import Update
from telegram.ext import Application, CommandHandler, ContextTypes


class CommandManager:
    _COMMANDS = {}

    def __init__(
        self, app: Application, ac_manager: AccessControlManager, logger: logging.Logger
    ):
        self.app = app
        self.ac_manager = ac_manager
        self.logger = logger
        self.__register_commands()
        self._register_command_handlers()

    def __init_subclass__(cls, **kwargs):
        super().__init_subclass__(**kwargs)
        cls.__register_commands()

    @classmethod
    def __register_commands(cls):
        """Register all command methods from the subclass."""

        def process_command_name(name):
            return name.replace("command_", "")

        cls._COMMANDS = {
            process_command_name(name): getattr(cls, name)
            for name in dir(cls)
            if name.startswith("command_")
        }
        cls.logger.info(f"Registered commands: {', '.join(cls._COMMANDS.keys())}")

    # Placeholder for command methods
    async def command_start(self, update: Update, context: ContextTypes.DEFAULT_TYPE):
        await context.bot.send_message(
            chat_id=update.effective_chat.id, text="Hello! I'm your bot."
        )

    async def command_help(self, update: Update, context: ContextTypes.DEFAULT_TYPE):
        """Sends a help message listing available commands based on the user's access."""
        user_id = update.effective_user.id
        available_commands = []

        # Iterate over registered commands to check access for each
        for command in self._COMMANDS.keys():
            if self.ac_manager.check_tg_command_access(str(user_id), command):
                available_commands.append(f"/{command}")

        help_text = "Available Commands:\n" + "\n".join(available_commands)
        await context.bot.send_message(chat_id=update.effective_chat.id, text=help_text)

    def _command_wrapper(self, func):
        """A decorator to wrap command methods for authorization and automatic command name inference."""
        command_name = func.__name__[len("command_") :]  # noqa E203

        @wraps(func)
        async def wrapper(
            update: Update, context: ContextTypes.DEFAULT_TYPE, *args, **kwargs
        ):
            self.logger.info(f"Command triggered: {command_name}")
            user_id = update.effective_user.id

            if self.ac_manager.check_tg_command_access(str(user_id), command_name):
                return await func(self, update, context, *args, **kwargs)
            else:
                logging.warning(
                    f"Unauthorized access attempted from {update.effective_user}"
                )
                await context.bot.send_message(
                    chat_id=update.effective_chat.id,
                    text="You are not authorized to use this command.",
                )

        return wrapper

    def _register_command_handlers(self):
        """Registers all bot commands based on methods named with the 'command_' prefix."""
        for command_name, method in self._COMMANDS.items():
            wrapped_method = self._command_wrapper(method)
            self.logger.info(f"Registering command: {command_name}")
            self.app.add_handler(CommandHandler(command_name, wrapped_method))
