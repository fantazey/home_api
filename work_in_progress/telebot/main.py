"""
Бот для записи времени по покрасу через телеграм
необходимый функционал:
- записать время
- сохранить фотку в запись времени
- сохранить фотку в модель
- обновить запись времени
- удалить запись времени
"""
import logging
import re

from telegram import Update
from telegram.ext import ApplicationBuilder, CommandHandler, ContextTypes, MessageHandler, filters, CallbackQueryHandler

from home_api.private_settings import TOKEN, TEST_TOKEN, DEBUG
from .handlers import start_handler, keyboard_handler, handler_progress_add, handler_image_add, \
    handler_model_buy, handler_model_want, error_handler, handler_hangar_light, model_keyboard_handler, \
    progress_keyboard_handler


logging.basicConfig(
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s',
    level=logging.ERROR
)


async def start(update: Update, context: ContextTypes.DEFAULT_TYPE):
    return await start_handler(update, context)


async def keyboard(update: Update, context: ContextTypes.DEFAULT_TYPE):
    return await keyboard_handler(update, context)


async def model_keyboard(update: Update, context: ContextTypes.DEFAULT_TYPE):
    return await model_keyboard_handler(update, context)


async def progress_keyboard(update: Update, context: ContextTypes.DEFAULT_TYPE):
    return await progress_keyboard_handler(update, context)


async def progress(update: Update, context: ContextTypes.DEFAULT_TYPE):
    return await handler_progress_add(update, context)


async def upload_photo(update: Update, context: ContextTypes.DEFAULT_TYPE):
    return await handler_image_add(update, context)


async def add_model(update: Update, context: ContextTypes.DEFAULT_TYPE):
    return await handler_model_buy(update, context)


async def want_model(update: Update, context: ContextTypes.DEFAULT_TYPE):
    return await handler_model_want(update, context)


async def hangar_light(update: Update, context: ContextTypes.DEFAULT_TYPE):
    return await handler_hangar_light(update, context)


async def error(update: Update, context: ContextTypes.DEFAULT_TYPE):
    return await error_handler(update, context)


def run_telebot():
    application = ApplicationBuilder().token(TOKEN).build()
    application.add_handler(CommandHandler('start', start))
    application.add_handler(MessageHandler(filters.PHOTO, upload_photo))

    progress_pattern = re.compile(r"^progress.*$")
    application.add_handler(CallbackQueryHandler(progress_keyboard, pattern=progress_pattern))

    model_pattern = re.compile(r"^model.*$")
    application.add_handler(CallbackQueryHandler(model_keyboard, pattern=model_pattern))

    application.add_handler(CallbackQueryHandler(keyboard))

    time_pattern = re.compile(r"^(\d+\.?\d*ч)|(\d+\.?\d*м).*", flags=re.IGNORECASE)
    application.add_handler(MessageHandler(filters.Regex(time_pattern), progress))

    buy_pattern = re.compile(r"^купил .*", flags=re.IGNORECASE)
    application.add_handler(MessageHandler(filters.Regex(buy_pattern), add_model))

    want_pattern = re.compile(r"^хочу .*", flags=re.IGNORECASE)
    application.add_handler(MessageHandler(filters.Regex(want_pattern), want_model))

    light_pattern = re.compile(r"^свет .*", flags=re.IGNORECASE)
    application.add_handler(MessageHandler(filters.Regex(light_pattern), hangar_light))

    application.add_error_handler(error)

    application.run_polling()


if __name__ == '__main__':
    run_telebot()
