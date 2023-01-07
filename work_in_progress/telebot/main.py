import io
import logging

from asgiref.sync import sync_to_async
from django.db.models import Max
from django.utils import timezone
from django.core.files.images import ImageFile
from telegram import Update
from telegram.ext import ApplicationBuilder, CommandHandler, ContextTypes, MessageHandler, filters

from home_api.private_settings import TOKEN
from work_in_progress.models import Model, ModelProgress, ModelImage, Artist

CHAT_PROGRESS_RECORDS = {}

logging.basicConfig(
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s',
    level=logging.DEBUG
)


@sync_to_async
def get_artist(telegram_name):
    return Artist.objects.filter(telegram_name=telegram_name).first()


async def start_command(update: Update, context: ContextTypes.DEFAULT_TYPE):
    artist_exists = await get_artist(update.effective_chat.username)
    if not artist_exists:
        await context.bot.send_message(chat_id=update.effective_chat.id,
                                       text="Пользователь %s не найден" % update.effective_chat.username)
        return
    await context.bot.send_message(chat_id=update.effective_chat.id, text="\n".join(HELP_TEXT))


HELP_TEXT = [
    'Чтобы посмотреть помощь используй команду\n/help',
    'Чтобы записать время используй команду\n/time id-модели время [описание]\nнапример /time 1 4.5 покрасил пушку'
]


async def help_command(update: Update, context: ContextTypes.DEFAULT_TYPE):
    await context.bot.send_message(chat_id=update.effective_chat.id, text=''.join(HELP_TEXT))


@sync_to_async
def get_user_models(username):
    artists = Artist.objects.filter(telegram_name=username)
    if artists.count() != 1:
        raise Exception("Найдено 0 или больше 1 пользователя")

    user = artists.first().user
    models = Model.objects.annotate(
        last_record=Max('modelprogress__datetime')
    ).filter(user=user).order_by('-last_record')[:5]
    result = []
    for model in models:
        result.append({
            'id': model.id,
            'name': model.name,
            'status': model.get_status_display()
        })
    return result


@sync_to_async()
def get_model(model_id):
    return Model.objects.get(id=model_id)


@sync_to_async
def get_model_progress(progress_id):
    return ModelProgress.objects.get(id=progress_id)


@sync_to_async
def record_model_progress(model_id, time, title, telegram_name):
    artist = Artist.objects.filter(telegram_name=telegram_name).first()
    user = artist.user
    model = Model.objects.filter(id=model_id, user=user).first()
    progress = ModelProgress(model=model,
                             status=model.status,
                             time=time,
                             title=title,
                             datetime=timezone.now())
    progress.save()
    return progress.id


@sync_to_async
def save_image_to_progress(model_progress_id, image_file):
    model_progress = ModelProgress.objects.get(id=model_progress_id)
    image = ModelImage(image=image_file, progress=model_progress, model=model_progress.model)
    image.save()


async def time_command(update: Update, context: ContextTypes.DEFAULT_TYPE):
    if context.args is None or len(context.args) == 0:
        models = await get_user_models(update.effective_chat.username)
        text = []
        for model in models:
            message = "Чтобы записать время для модели %s (%s) используй команду: \n/time %s время [описание]" % \
                      (model['name'], model['status'], model['id'])
            text.append(message)
        await context.bot.send_message(chat_id=update.effective_chat.id, text="\n".join(text))
        return
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
    message = ["Записал время %s часов для модели %s" % (track_time, model_id)]
    title = ""
    if len(context.args) > 3:
        title = " ".join(context.args[2:])
        message.append("C пояснением %s" % title)
    model_progress_id = await record_model_progress(model_id, track_time, title, update.effective_chat.username)
    message.append("ид записи: %s" % model_progress_id)
    CHAT_PROGRESS_RECORDS[update.effective_chat.id] = model_progress_id
    message.append("Чтобы добавить фотографию к записанному времени отправь в ответ файл")
    await context.bot.send_message(chat_id=update.effective_chat.id, text="\n".join(message))


async def upload_photo(update: Update, context: ContextTypes.DEFAULT_TYPE):
    if update.effective_chat.id not in CHAT_PROGRESS_RECORDS.keys():
        await context.bot.send_message(chat_id=update.effective_chat.id,
                                       text="Не достаточно контекста для сохранения фотографии")
    if not update.message.document and not update.message.photo:
        await context.bot.send_message(chat_id=update.effective_chat.id, text="Непонятно")
        return

    model_progress_id = CHAT_PROGRESS_RECORDS[update.effective_chat.id]
    del CHAT_PROGRESS_RECORDS[update.effective_chat.id]

    bot = update.get_bot()
    buf = bytearray()
    file_id = None
    if update.message.document:
        document = update.message.document
        file_id = document.file_id
    if update.message.photo:
        count = len(update.message.photo)
        file_id = update.message.photo[count - 1].file_id

    if file_id is not None:
        file = await bot.get_file(file_id)
        file_name = update.effective_chat.username + "_" + file_id
        await file.download_as_bytearray(buf)
        print(file_id, file_name, buf)
        image_file = ImageFile(io.BytesIO(buf), name=file_name)
        await save_image_to_progress(model_progress_id, image_file)
        await context.bot.send_message(chat_id=update.effective_chat.id, text="Картиночка сохранена")


def run_telebot():
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


if __name__ == '__main__':
    run_telebot()
