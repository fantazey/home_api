"""
Бот для записи времени по покрасу через телеграм
необходимый функционал:
- записать время
- сохранить фотку в запись времени
- сохранить фотку в модель
- обновить запись времени
- удалить запись времени
"""
import io
import logging

from asgiref.sync import sync_to_async
from django.db.models import Max, QuerySet
from django.utils import timezone
from django.core.files.images import ImageFile
from django.contrib.auth.models import User
from telegram import Update
from telegram.ext import ApplicationBuilder, CommandHandler, ContextTypes, MessageHandler, filters

from home_api.private_settings import TOKEN
from work_in_progress.models import Model, ModelProgress, ModelImage, Artist

CHAT_PROGRESS_RECORDS = {}
CHAT_MODEL_RECORDS = {}

logging.basicConfig(
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s',
    level=logging.DEBUG
)


async def start_command(update: Update, context: ContextTypes.DEFAULT_TYPE):
    await get_user(update.effective_chat.username)
    await context.bot.send_message(chat_id=update.effective_chat.id, text="\n".join(HELP_TEXT))


HELP_TEXT = [
    'Чтобы посмотреть помощь - \n/help',
    'Чтобы вывести 5 последних моделей над которыми велась работа - \n/models',
    'Чтобы записать время - \n"/progress id-модели время [описание]\n"' +
    'например "/progress 1 4.5 покрасил пушку"',
    'Чтобы добавить фотографию к записанному времени - "/progress_photo id-записи вемени"',
    'Чтобы добавить фотографию к модели - "/model_photo id-модели"'
]


async def help_command(update: Update, context: ContextTypes.DEFAULT_TYPE):
    await context.bot.send_message(chat_id=update.effective_chat.id, text=''.join(HELP_TEXT))


async def models_command(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """
    Вывести 5 последних моделей над которыми шла работа
    :param update:
    :param context:
    :return:
    """
    models = await get_user_models(update.effective_chat.username)
    text = []
    for model in models:
        message = "Чтобы записать время для модели %s (%s) - \"/progress %s время [описание]\"" % \
                  (model['name'], model['status'], model['id'])
        text.append(message)
    await context.bot.send_message(chat_id=update.effective_chat.id, text="\n".join(text))


async def progress_command(update: Update, context: ContextTypes.DEFAULT_TYPE):
    if len(context.args) < 2:
        await context.bot.send_message(chat_id=update.effective_chat.id,
                                       text="Мало данных, нужно указать ид модели и время, описание опционально")
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
    model_progress_id = await record_model_progress(update.effective_chat.username, model_id, track_time, title)
    message.append("id записи для прикрепления фото: %s (командой \"/progress_photo %s\")" %
                   (model_progress_id, model_progress_id))
    await context.bot.send_message(chat_id=update.effective_chat.id, text="\n".join(message))


async def progress_photo_command(update: Update, context: ContextTypes.DEFAULT_TYPE):
    model_progress_id = int(context.args[0])
    model_progress = await get_model_progress(update.effective_chat.username, model_progress_id)
    model = model_progress.model
    message = "Чтобы добавить картинку к записи времени %s для модели %s отправь фото в чат" % (
        model_progress, model
    )
    CHAT_PROGRESS_RECORDS[update.effective_chat.id] = model_progress_id
    await context.bot.send_message(chat_id=update.effective_chat.id, text=message)


async def upload_photo(update: Update, context: ContextTypes.DEFAULT_TYPE):
    is_progress_photo = update.effective_chat.id in CHAT_PROGRESS_RECORDS.keys()
    is_model_photo = update.effective_chat.id in CHAT_PROGRESS_RECORDS.keys()
    if not is_progress_photo and not is_model_photo:
        message = "Не достаточно контекста для сохранения фотографии. " \
                  "Выполни команды \"/progress_photo id\" или \"/model_photo id\""
        await context.bot.send_message(chat_id=update.effective_chat.id,
                                       text=message)
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


@sync_to_async
def get_user(telegram_name) -> User:
    """
    Получить пользователя по нику в телеге
    :param telegram_name:
    :return: пользователь
    """
    artists = Artist.objects.filter(telegram_name=telegram_name)
    if artists.count() != 1:
        raise Exception("Найдено 0 или больше 1 пользователя")
    return artists.first().user


@sync_to_async
def get_user_models(telegram_name) -> list[dict]:
    """
    Получить список последних 5 моделей в работе
    :param telegram_name:
    :return:
    """
    user = get_user(telegram_name)
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
def get_model(model_id) -> Model:
    """
    Получить модель по ид
    :param model_id:
    :return:
    """
    return Model.objects.get(id=model_id)


@sync_to_async
def get_model_progress(telegram_name: str, progress_id: int) -> ModelProgress:
    """
    Получить объект записи времени по ид
    :param telegram_name:
    :param progress_id:
    :return:
    """
    user = get_user(telegram_name)
    return ModelProgress.objects.get(id=progress_id, model__user=user)


@sync_to_async
def record_model_progress(telegram_name: str, model_id: int, time: int, title: str) -> int:
    """
    Запись времени работы над моделью
    :param telegram_name:
    :param model_id:
    :param time:
    :param title:
    :return:
    """
    user = get_user(telegram_name)
    model = Model.objects.filter(id=model_id, user=user).first()
    progress = ModelProgress(model=model,
                             status=model.status,
                             time=time,
                             title=title,
                             datetime=timezone.now())
    progress.save()
    return progress.id


@sync_to_async
def save_image_to_progress(telegram_name: str, model_progress_id: int, image_file):
    user = get_user(telegram_name)
    model_progress = ModelProgress.objects.get(id=model_progress_id, model__user=user)
    image = ModelImage(image=image_file, progress=model_progress, model=model_progress.model)
    image.save()


def run_telebot():
    application = ApplicationBuilder().token(TOKEN).build()
    start_handler = CommandHandler('start', start_command)
    application.add_handler(start_handler)

    help_handler = CommandHandler('help', help_command)
    application.add_handler(help_handler)

    models_handler = CommandHandler('models', models_command)
    application.add_handler(models_handler)

    progress_handler = CommandHandler('progress', progress_command)
    application.add_handler(progress_handler)

    image_handler = MessageHandler(filters.PHOTO, upload_photo)  # | filters.Document.JPG | filters.Document.IMAGE,
    application.add_handler(image_handler)

    application.run_polling()


if __name__ == '__main__':
    run_telebot()
