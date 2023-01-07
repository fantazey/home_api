import logging

from telegram import Update
from telegram.ext import ApplicationBuilder, CommandHandler, ContextTypes, MessageHandler, filters

from home_api.private_settings import TOKEN

CHAT_PROGRESS_RECORDS = {}

logging.basicConfig(
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s',
    level=logging.DEBUG
)


async def start_command(update: Update, context: ContextTypes.DEFAULT_TYPE):
    await context.bot.send_message(chat_id=update.effective_chat.id, text="".join(HELP_TEXT))


HELP_TEXT = [
    'Чтобы посмотреть помощь используй команду\n/help',
    'Чтобы записать время используй команду\n/time'
]


async def help_command(update: Update, context: ContextTypes.DEFAULT_TYPE):
    await context.bot.send_message(chat_id=update.effective_chat.id, text=''.join(HELP_TEXT))


def get_user_models(username):
    return [
        {'id': 1, 'name': 'Test 1', 'status': 'Painting'},
        {'id': 2, 'name': 'Test 2', 'status': 'Highlighting'},
        {'id': 3, 'name': 'Test 3', 'status': 'Assembling'}
    ]


def get_track_record(progress_id):
    return {"id": 1, "title": "123", "time": "123"}


async def time_command(update: Update, context: ContextTypes.DEFAULT_TYPE):
    if context.args is None or len(context.args) == 0:
        # todo: добавить чтение моделей из базы
        models = get_user_models(update.effective_chat.username)
        text = []
        for model in models:
            message = "Чтобы записать время для модели %s (%s) используй команду: \n/time %s" % \
                      (model['name'], model['status'], model['id'])
            text.append(message)
        await context.bot.send_message(chat_id=update.effective_chat.id, text="\n".join(text))

    if len(context.args) < 2:
        await context.bot.send_message(chat_id=update.effective_chat.id, text="Мало данных")
        return
    try:
        model_id = int(context.args[0])
        track_time = float(context.args[1].replace(',', '.'))
    except ValueError:
        await context.bot.send_message(chat_id=update.effective_chat.id,
                                       text="Первый и второй параметры должны быть числами: 1 или 0.5 или 0,5")
        return
    message = ["Записываю время %s часов для модели %s" % (track_time, model_id)]
    if len(context.args) > 3:
        title = " ".join(context.args[2:])
        message.append("C пояснением %s" % title)

    # todo: Сохранить запись в базу
    track_record_id = 1
    CHAT_PROGRESS_RECORDS[update.effective_chat.id] = track_record_id
    message.append("Чтобы добавить фотографию к записанному времени отправь в ответ файл")
    await context.bot.send_message(chat_id=update.effective_chat.id, text="\n".join(message))


async def upload_photo(update: Update, context: ContextTypes.DEFAULT_TYPE):
    if update.effective_chat.id not in CHAT_PROGRESS_RECORDS.keys():
        await context.bot.send_message(chat_id=update.effective_chat.id,
                                       text="Не достаточно контекста для сохранения фотографии")
    track_id = CHAT_PROGRESS_RECORDS[update.effective_chat.id]
    get
    message = [""]
    bot = update.get_bot()
    caption = update.message.caption
    if update.message.document:
        document = update.message.document
        file_id = document.file_id
        file_name = document.file_name
        file_size = document.file_size
        file = await bot.get_file(file_id)
        buf = None
        await file.download_as_bytearray(buf)
        print(file_id, file_size, file_name, buf)
        await context.bot.send_message(chat_id=update.effective_chat.id, text="Загружаю документ %s" % file_name)
        return
    if update.message.photo:
        # photo = update.message.photo
        count = len(update.message.photo)
        file_id = update.message.photo[count-1].file_id
        file_size = update.message.photo[count - 1].file_size
        file_name = update.effective_chat.username + " " + file_id
        file = await bot.get_file(file_id)
        buf = None
        await file.download_as_bytearray(buf)
        print(file_id, file_size, file_name, buf)
        await context.bot.send_message(chat_id=update.effective_chat.id, text="Загружаю фото %s" % file_name)
        return
    await context.bot.send_message(chat_id=update.effective_chat.id, text="Непонятно")

if __name__ == '__main__':
    application = ApplicationBuilder().token(TOKEN).build()
    start_handler = CommandHandler('start', start_command)
    time_handler = CommandHandler('time', time_command)
    help_handler = CommandHandler('help', help_command)
    image_handler = MessageHandler(filters.PHOTO, upload_photo)  # | filters.Document.JPG | filters.Document.IMAGE,
    application.add_handler(start_handler)
    application.add_handler(help_handler)
    application.add_handler(time_handler)
    application.add_handler(image_handler)
    application.run_polling()
