import logging
import os

from telegram import Update, InlineKeyboardMarkup, InlineKeyboardButton
from telegram.ext import CommandHandler, MessageHandler, filters, Application, ContextTypes, \
    CallbackQueryHandler, CallbackContext
from google.cloud import dialogflow
from google.api_core.exceptions import InvalidArgument

from config import CONFIG
from lang.language import Language

# Enable logging
logging.basicConfig(
    format="%(asctime)s - %(name)s - %(levelname)s - %(message)s", level=logging.INFO
)
logging.getLogger("httpx").setLevel(logging.WARNING)
logger = logging.getLogger(__name__)


class TelegramBot:
    def __init__(self, telegram_token, dialogflow_credentials_path, dialogflow_project_id, language: Language):
        self.language = language
        self.telegram_token = telegram_token
        self.dialogflow_credentials_path = dialogflow_credentials_path
        self.dialogflow_project_id = dialogflow_project_id
        os.environ["GOOGLE_CLOUD_PROJECT"] = self.dialogflow_project_id
        os.environ["GOOGLE_APPLICATION_CREDENTIALS"] = self.dialogflow_credentials_path
        self.dialogflow_session_client = dialogflow.SessionsClient()

    def detect_intent_from_text(self, text, session_id) -> dict:
        session = self.dialogflow_session_client.session_path(self.dialogflow_project_id, session_id)
        text_input = dialogflow.TextInput(text=text, language_code=self.language.lang)
        query_input = dialogflow.QueryInput(text=text_input)
        try:
            response = self.dialogflow_session_client.detect_intent(session=session, query_input=query_input)
        except InvalidArgument:
            raise

        return {
            "intent": response.query_result.intent.display_name,
            "text": response.query_result.fulfillment_text
        }

    async def income_msg(self, update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
        self.set_language(update.message.from_user.language_code)
        result = self.detect_intent_from_text(update.message.text, update.message.from_user.id)
        logger.info(update)
        logger.info(result)
        await update.message.reply_text(str(result['text']))
        if result['intent'] == 'dialog.end' or result['intent'] == 'dialog.start':
            if result['intent'] == 'dialog.end':
                await update.message.reply_text(self.language.get_text('end_msg'))

            await self.help_command(update, context, 'second_msg')

    async def button_click(self, update: Update, context: CallbackContext) -> None:
        query = update.callback_query
        await query.answer()

        if query.data == 'button_documents':
            await query.edit_message_text(text="click Some documents")
            # await update.message.reply_text("click documents")
        elif query.data == 'button_set_up_you_company':
            await query.edit_message_text(text="click Set up company")
            # await update.message.reply_text("click Set up company")
        elif query.data == 'taxation':
            await query.edit_message_text(text="click Taxation")
            # await update.message.reply_text("click Taxation")

    def set_language(self, lang):
        if lang == 'ru':
            self.language.set_lang(lang)
        else:
            self.language.set_lang('en')

    # /help
    async def help_command(self, update, context, text='help'):
        self.set_language(update.message.from_user.language_code)
        keyboard = [
            [InlineKeyboardButton(language.get_text('button_documents'), callback_data='button_documents')],
            [InlineKeyboardButton(language.get_text('button_set_up_you_company'), callback_data='button_set_up_you_company')],
            [InlineKeyboardButton(language.get_text('taxation'), callback_data='taxation')],
        ]
        reply_markup = InlineKeyboardMarkup(keyboard)
        await update.message.reply_text(language.get_text(text), reply_markup=reply_markup)

    # /start
    async def start_command(self, update, context):
        self.set_language(update.message.from_user.language_code)
        await update.message.reply_text(language.get_text('start'))
        await self.help_command(update, context, 'second_msg')

    def run(self):
        application = Application.builder().token(self.telegram_token).build()
        application.add_handler(CommandHandler("start", self.start_command))
        application.add_handler(CommandHandler("help", self.help_command))
        application.add_handler(CallbackQueryHandler(self.button_click))
        application.add_handler(MessageHandler(filters.TEXT, self.income_msg))
        application.run_polling(allowed_updates=Update.ALL_TYPES)


if __name__ == '__main__':
    telegram_token = CONFIG['telegram_token']
    dialogflow_credentials_path = CONFIG['dialogflow']['credentials_path']
    dialogflow_project_id = CONFIG['dialogflow']['project_id']
    language = Language()

    bot = TelegramBot(telegram_token, dialogflow_credentials_path, dialogflow_project_id, language)
    bot.run()
    print('end')
