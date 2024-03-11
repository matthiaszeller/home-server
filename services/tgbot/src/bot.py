from telegram.ext import ApplicationBuilder, CommandHandler, ContextTypes

from common.config import PathRegistry as PR
from common import utils


class TelegramBot:

    PATH_TOKEN = PR.get_config_file('secrets/bot_api.txt')

    def __init__(self):
        self.token = utils.read_text_file(self.PATH_TOKEN)

    async def start(self, update, context: ContextTypes.DEFAULT_TYPE):
        await context.bot.send_message(chat_id=update.effective_chat.id, text="Hello! I'm your bot.")

    def error_handler(self, update, context):
        # Log Errors caused by Updates or notify users of error, etc.
        print(f"Error occurred: {context.error}")

    def run(self):
        # Create Application and pass token
        application = ApplicationBuilder().token(self.token).build()

        # Add handlers
        start_handler = CommandHandler('start', self.start)
        application.add_handler(start_handler)

        # Add error handler
        application.add_error_handler(self.error_handler)

        # Run the bot
        application.run_polling()


def run_bot():
    bot = TelegramBot()
    bot.run()
