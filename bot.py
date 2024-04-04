import logging
import os
from warnings import filterwarnings

from telegram import Update, InlineKeyboardMarkup, InlineKeyboardButton
from telegram.ext import CommandHandler, MessageHandler, filters, Application, ContextTypes, \
    CallbackQueryHandler, CallbackContext, ConversationHandler
from google.cloud import dialogflow
from google.api_core.exceptions import InvalidArgument
from telegram.warnings import PTBUserWarning

from config import CONFIG
from lang.language import Language

filterwarnings(action="ignore", message=r".*CallbackQueryHandler", category=PTBUserWarning)

# Enable logging
logging.basicConfig(
    format="%(asctime)s - %(name)s - %(levelname)s - %(message)s", level=logging.INFO
)
logging.getLogger("httpx").setLevel(logging.WARNING)
logger = logging.getLogger(__name__)

START_ROUTES, END_ROUTES = range(2)

DOCUMENTS, COMPANY, TAXATION, = range(3)

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

            await self.help(update, context, 'second_msg')

    def set_language(self, lang):
        if lang == 'ru':
            self.language.set_lang(lang)
        else:
            self.language.set_lang('en')

    # /help
    async def help(self, update, context, text='help'):
        self.set_language(update.message.from_user.language_code)
        keyboard = [
            [InlineKeyboardButton(language.get_text('button_documents'), callback_data="documents")],
            [InlineKeyboardButton(language.get_text('button_set_up_you_company'), callback_data="company")],
            [InlineKeyboardButton(language.get_text('button_taxation'), callback_data="taxation")],
        ]
        reply_markup = InlineKeyboardMarkup(keyboard)
        await update.message.reply_text(language.get_text(text), reply_markup=reply_markup)
        return START_ROUTES

    # /start
    async def start(self, update, context):
        self.set_language(update.message.from_user.language_code)
        await update.message.reply_text(language.get_text('start'))
        return await self.help(update, context, 'second_msg')

    # documents
    async def documents(self, update, context):
        query = update.callback_query
        await query.answer()
        keyboard = [
            [
                InlineKeyboardButton(self.language.get_text("documents_visa_bnt"), callback_data="documents_visa_bnt"),
                InlineKeyboardButton(self.language.get_text("documents_police_bnt"), callback_data="documents_police_bnt"),
            ],
            [
                InlineKeyboardButton(self.language.get_text("documents_translation_btn"), callback_data="documents_translation_btn"),
                InlineKeyboardButton(self.language.get_text("company_another_bnt"), callback_data="company_another_bnt"),
            ]
        ]
        reply_markup = InlineKeyboardMarkup(keyboard)
        # await context.bot.send_message(chat_id=query.from_user.id, text=self.language.get_text('documents'))
        await query.edit_message_text(
            text=language.get_text('documents') + "\n" + language.get_text('documents_2'), reply_markup=reply_markup
        )

    async def documents_visa_bnt(self, update, context):
        query = update.callback_query
        await query.answer()
        keyboard = [
            [
                InlineKeyboardButton(self.language.get_text("back"), callback_data="documents"),
                InlineKeyboardButton(self.language.get_text("thanks"), callback_data="more_question")
            ]
        ]
        reply_markup = InlineKeyboardMarkup(keyboard)
        await query.edit_message_text(text=language.get_text('documents_visa'), reply_markup=reply_markup)

    async def documents_police_bnt(self, update, context):
        query = update.callback_query
        await query.answer()
        keyboard = [
            [
                InlineKeyboardButton(self.language.get_text("back"), callback_data="documents"),
                InlineKeyboardButton(self.language.get_text("thanks"), callback_data="more_question")
            ]
        ]
        reply_markup = InlineKeyboardMarkup(keyboard)
        await query.edit_message_text(text=language.get_text('documents_police'), reply_markup=reply_markup)

    async def documents_translation_btn(self, update, context):
        query = update.callback_query
        await query.answer()
        keyboard = [
            [
                InlineKeyboardButton(self.language.get_text("back"), callback_data="documents"),
                InlineKeyboardButton(self.language.get_text("thanks"), callback_data="more_question")
            ]
        ]
        reply_markup = InlineKeyboardMarkup(keyboard)
        await query.edit_message_text(text=language.get_text('documents_translation'), reply_markup=reply_markup)

    async def documents_another_btn(self, update, context):
        query = update.callback_query
        await query.answer()
        await query.edit_message_text(text=language.get_text('company_another_text'))

    async def more_question(self, update, context):
        query = update.callback_query
        await query.answer()
        keyboard = [
            [InlineKeyboardButton(language.get_text('button_documents'), callback_data="documents")],
            [InlineKeyboardButton(language.get_text('button_set_up_you_company'), callback_data="company")],
            [InlineKeyboardButton(language.get_text('button_taxation'), callback_data="taxation")],
        ]
        reply_markup = InlineKeyboardMarkup(keyboard)
        await query.edit_message_text(text=language.get_text('more_question'), reply_markup=reply_markup)

    # company
    async def company(self, update, context):
        query = update.callback_query
        await query.answer()
        keyboard = [
            [
                InlineKeyboardButton(self.language.get_text("company_types_btn"), callback_data="company_types_btn"),
                InlineKeyboardButton(self.language.get_text("company_reg_btn"), callback_data="company_reg_btn"),
            ],
            [
                InlineKeyboardButton(self.language.get_text("company_payments_btn"), callback_data="company_payments_btn"),
                InlineKeyboardButton(self.language.get_text("company_another_bnt"), callback_data="company_another_bnt"),
            ]
        ]
        reply_markup = InlineKeyboardMarkup(keyboard)
        await query.edit_message_text(
            text=language.get_text('company'), reply_markup=reply_markup
        )

    async def company_btn(self, update, context):
        query = update.callback_query
        await query.answer()
        await query.edit_message_text(text=language.get_text('company_res') + language.get_text(query.data))

    async def company_another_btn(self, update, context):
        query = update.callback_query
        await query.answer()
        await query.edit_message_text(text=language.get_text('company_another_text'))

    # taxation
    async def taxation(self, update, context):
        query = update.callback_query
        await query.answer()
        keyboard = [
            [
                InlineKeyboardButton(self.language.get_text("taxation_tax_btn"), callback_data="taxation_tax_btn"),
                InlineKeyboardButton(self.language.get_text("taxation_calc_btn"), callback_data="taxation_calc_btn"),
            ],
            [
                InlineKeyboardButton(self.language.get_text("taxation_individual_btn"), callback_data="taxation_individual_btn"),
                InlineKeyboardButton(self.language.get_text("taxation_another_bnt"), callback_data="taxation_another_bnt"),
            ]
        ]
        reply_markup = InlineKeyboardMarkup(keyboard)
        await query.edit_message_text(
            text=language.get_text('taxation'), reply_markup=reply_markup
        )

    async def taxation_btn(self, update, context):
        query = update.callback_query
        await query.answer()
        await query.edit_message_text(text=language.get_text('taxation_res') + language.get_text(query.data))

    async def taxation_another_btn(self, update, context):
        query = update.callback_query
        await query.answer()
        await query.edit_message_text(text=language.get_text('taxation_another_text'))

    def run(self):
        application = Application.builder().token(self.telegram_token).build()

        conv_handler = ConversationHandler(
            entry_points=[CommandHandler("start", self.start)],
            states={
                START_ROUTES:[
                    CallbackQueryHandler(self.documents, pattern="^documents$"),
                    CallbackQueryHandler(self.documents_visa_bnt, pattern="^documents_visa_bnt$"),
                    CallbackQueryHandler(self.documents_police_bnt, pattern="^documents_police_bnt$"),
                    CallbackQueryHandler(self.documents_translation_btn, pattern="^documents_translation_btn$"),
                    CallbackQueryHandler(self.company_another_btn, pattern="^documents_another_bnt$"),
                    CallbackQueryHandler(self.more_question, pattern="^more_question"),
                    # company
                    CallbackQueryHandler(self.company, pattern="^company$"),
                    CallbackQueryHandler(self.company_btn, pattern="^company_types_btn$"),
                    CallbackQueryHandler(self.company_btn, pattern="^company_reg_btn$"),
                    CallbackQueryHandler(self.company_btn, pattern="^company_payments_btn$"),
                    CallbackQueryHandler(self.company_another_btn, pattern="^company_another_bnt$"),
                    # taxation
                    CallbackQueryHandler(self.taxation, pattern="^taxation$"),
                    CallbackQueryHandler(self.taxation_btn, pattern="^taxation_tax_btn$"),
                    CallbackQueryHandler(self.taxation_btn, pattern="^taxation_calc_btn$"),
                    CallbackQueryHandler(self.taxation_btn, pattern="^taxation_individual_btn$"),
                    CallbackQueryHandler(self.taxation_another_btn, pattern="^taxation_another_bnt$"),
                ],
            },
            fallbacks=[CommandHandler("start", self.start)],
        )

        application.add_handler(conv_handler)
        application.add_handler(CommandHandler("help", self.help))
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
