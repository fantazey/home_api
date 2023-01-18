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
import re

from asgiref.sync import sync_to_async
from django.db.models import Max
from django.utils import timezone
from django.core.files.images import ImageFile
from django.contrib.auth.models import User
from telegram import Update
from telegram.ext import ApplicationBuilder, CommandHandler, ContextTypes, MessageHandler, filters

from home_api.private_settings import TOKEN
from work_in_progress.templatetags.wip_filters import duration
from work_in_progress.models import Model, ModelProgress, ModelImage, Artist

CHAT_PROGRESS_RECORDS = {}
CHAT_MODEL_RECORDS = {}

logging.basicConfig(
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s',
    level=logging.DEBUG
)


async def start_command(update: Update, context: ContextTypes.DEFAULT_TYPE):
    try:
        await get_user(update.effective_chat.username)
    except Exception as ex:
        await context.bot.send_message(chat_id=update.effective_chat.id, text=ex.args[0])
        return
    await context.bot.send_message(chat_id=update.effective_chat.id, text="\n".join(HELP_TEXT))


HELP_TEXT = [
    'Чтобы посмотреть помощь - \n/help',
    'Чтобы вывести 5 последних моделей над которыми велась работа - \n/list_models',
    'Чтобы вывести 5 последних записей о покрасе по модели над которой велась работа - \n/list_progress id-модели',
    'Чтобы записать время - \n/progress id-модели время [описание]\n' +
    'например "/progress 1 4.5 покрасил пушку"',
    'Чтобы добавить фотографию к записанному времени - \n/progress_photo id-записи вемени\n' +
    'например "/progress_photo 219"',
    'Чтобы добавить фотографию к модели - \n/model_photo id-модели\nнапример "/model_photo 100"'
]


async def help_command(update: Update, context: ContextTypes.DEFAULT_TYPE):
    await context.bot.send_message(chat_id=update.effective_chat.id, text='\n'.join(HELP_TEXT))


async def list_models_command(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """
    Вывести 5 последних моделей над которыми шла работа
    :param update:
    :param context:
    :return:
    """
    try:
        user = await get_user(update.effective_chat.username)
    except Exception as ex:
        await context.bot.send_message(chat_id=update.effective_chat.id, text=ex.args[0])
        return

    models = await get_user_models(user)
    if len(models) == 0:
        await context.bot.send_message(chat_id=update.effective_chat.id, text="Нет ни одной модели")
        return

    text = []
    for model in models:
        text.append("%s - %s (%s)" % (model['id'], model['name'], model['status']))
    await context.bot.send_message(chat_id=update.effective_chat.id, text="\n".join(text))


async def list_progress_command(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """
    Вывести записи 5 последних работ для модели по id
    :param update:
    :param context:
    :return:
    """
    if len(context.args) != 1:
        await context.bot.send_message(chat_id=update.effective_chat.id, text="Надо указать ид модели")
    model_id = int(context.args[0])
    try:
        user = await get_user(update.effective_chat.username)
    except Exception as ex:
        await context.bot.send_message(chat_id=update.effective_chat.id, text=ex.args[0])
        return

    try:
        model = await get_model(user, model_id)
    except Model.DoesNotExist:
        await context.bot.send_message(chat_id=update.effective_chat.id, text="Модель не надена")
        return

    progress_list = await get_model_progress_list(user, model)
    text = ["Работы по %s:" % model]
    for progress in progress_list:
        text.append("%s - %s %s |%s" % (progress['id'], progress['title'], progress['time'], progress['datetime']))
    await context.bot.send_message(chat_id=update.effective_chat.id, text="\n".join(text))


async def progress_command(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """
    Записать время в работу над моделью
    ожидаемые аргументы в context:
    1 - ид модели
    2 - время в часах(десятичная часть через точку или запятую)
    3... все оставшиеся аргументы трактуются как описание
    :param update:
    :param context:
    :return:
    """
    if len(context.args) < 2:
        await context.bot.send_message(chat_id=update.effective_chat.id,
                                       text="Мало данных, нужно указать ид модели и время, описание опционально")
        return

    try:
        model_id = int(context.args[0])
        matcher = re.compile(r'((?P<hours>\d+)ч(ас)?\.?)?((?P<minutes>\d+)м(ин)?\.?)?')
        res = matcher.match(context.args[1])
        if len(res.groups()) > 0:
            track_time = float(res.group("hours") or 0) + (float(res.group("minutes") or 0)/60)
        else:
            track_time = float(context.args[1].replace(',', '.'))
    except ValueError:
        await context.bot.send_message(chat_id=update.effective_chat.id,
                                       text="Первый и второй параметры должны быть числами: " +
                                            "1 или 0.5 или 0,5 или 1ч15м или 1час20мин или 20мин или 1ч.30мин.")
        return

    message = ["Записал время %s часов для модели %s" % (track_time, model_id)]
    title = ""
    if len(context.args) > 3:
        title = " ".join(context.args[2:])
        message.append("C пояснением %s" % title)
    user = await get_user(update.effective_chat.username)
    try:
        model_progress_id = await record_model_progress(user, model_id, track_time, title)
    except Exception:
        await context.bot.send_message(chat_id=update.effective_chat.id, text="При создании записи возникла ошибка")
        return
    message.append("id записи для прикрепления фото: %s (командой \"/progress_photo %s\")" %
                   (model_progress_id, model_progress_id))
    await context.bot.send_message(chat_id=update.effective_chat.id, text="\n".join(message))


async def progress_photo_command(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """
    Инициировать процесс добавления фотографии к записи прогресса по модели
    :param update:
    :param context:
    :return:
    """
    try:
        model_progress_id = int(context.args[0])
    except IndexError:
        await context.bot.send_message(chat_id=update.effective_chat.id, text="Нужно указать ид модели")
        return
    except ValueError:
        await context.bot.send_message(chat_id=update.effective_chat.id, text="ид быть целым числом")
        return
    user = await get_user(update.effective_chat.username)
    try:
        model_progress = await get_model_progress(user, model_progress_id)
    except Exception:
        await context.bot.send_message(chat_id=update.effective_chat.id, text="Запись работы не найдена")
        return

    message = "Чтобы добавить картинку к записи времени %s %s для модели %s отправь фото в чат" % (
        model_progress['title'], model_progress['time'], model_progress['model_name']
    )
    CHAT_PROGRESS_RECORDS[update.effective_chat.id] = model_progress_id
    await context.bot.send_message(chat_id=update.effective_chat.id, text=message)


async def model_photo_command(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """
    Инициировать процесс добавления фотографии к модели
    :param update:
    :param context:
    :return:
    """
    model_id = int(context.args[0])
    user = get_user(update.effective_chat.username)
    try:
        model = await get_model(user, model_id)
    except Exception:
        await context.bot.send_message(chat_id=update.effective_chat.id, text="Модель не найдена")
        return
    message = "Чтобы добавить картинку для модели %s отправь фото в чат" % model.name
    CHAT_MODEL_RECORDS[update.effective_chat.id] = model_id
    await context.bot.send_message(chat_id=update.effective_chat.id, text=message)


async def upload_photo(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """
    Сохранение фото в базу
    :param update:
    :param context:
    :return:
    """
    is_progress_photo = update.effective_chat.id in CHAT_PROGRESS_RECORDS.keys()
    is_model_photo = update.effective_chat.id in CHAT_MODEL_RECORDS.keys()

    if not is_progress_photo and not is_model_photo:
        message = "Не достаточно контекста для сохранения фотографии. " \
                  "Выполни команды \"/progress_photo id\" или \"/model_photo id\""
        await context.bot.send_message(chat_id=update.effective_chat.id,
                                       text=message)
    if not update.message.document and not update.message.photo:
        await context.bot.send_message(chat_id=update.effective_chat.id, text="Непонятно")
        return

    model_progress_id = model_id = None

    if is_progress_photo:
        model_progress_id = CHAT_PROGRESS_RECORDS[update.effective_chat.id]
        del CHAT_PROGRESS_RECORDS[update.effective_chat.id]
    if is_model_photo:
        model_id = CHAT_MODEL_RECORDS[update.effective_chat.id]
        del CHAT_MODEL_RECORDS[update.effective_chat.id]

    bot = update.get_bot()
    buf = bytearray()
    file_id = None
    if update.message.document:
        document = update.message.document
        file_id = document.file_id
    if update.message.photo:
        count = len(update.message.photo)
        file_id = update.message.photo[count - 1].file_id

    if file_id is None:
        await context.bot.send_message(chat_id=update.effective_chat.id, text="Файл не найден")
        return

    file = await bot.get_file(file_id)
    file_name = update.effective_chat.username + "_" + file_id
    await file.download_as_bytearray(buf)
    image_file = ImageFile(io.BytesIO(buf), name=file_name)
    user = await get_user(update.effective_chat.username)
    try:
        await save_image_to_progress(user, model_id, model_progress_id, image_file)
    except Exception:
        await context.bot.send_message(chat_id=update.effective_chat.id, text="Ошибка сохранения картинки")
        return
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
        raise Exception("Пользователь не найден")
    return artists.first().user


@sync_to_async
def get_user_models(user: User) -> list[dict]:
    """
    Получить список последних 5 моделей в работе
    :param user:
    :return:
    """
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


@sync_to_async
def get_model(user: User, model_id: int) -> Model:
    """
    Получить модель по ид
    :param user:
    :param model_id:
    :return:
    """
    return Model.objects.get(id=model_id, user=user)


@sync_to_async
def get_model_progress(user: User, progress_id: int) -> dict:
    """
    Получить объект записи времени по ид
    :param user:
    :param progress_id:
    :return:
    """
    try:
        model_progress = ModelProgress.objects.get(id=progress_id, model__user=user)
    except ModelProgress.DoesNotExist:
        raise Exception("Запись не найдена")
    return {
        'id': model_progress.id,
        'model_id': model_progress.model.id,
        'title': model_progress.title,
        'time': duration(model_progress.time),
        'model_name': model_progress.model.name
    }


@sync_to_async
def get_model_progress_list(user: User, model: Model) -> list[dict]:
    progress_list = ModelProgress.objects.filter(model=model, model__user=user).order_by('-datetime')[:5]
    result = []
    for progress in progress_list:
        result.append({
            'id': progress.id,
            'title': progress.title,
            'time': duration(progress.time),
            'datetime': progress.datetime.strftime('%d-%m-%Y %H:%M:%S')
        })
    return result


@sync_to_async
def record_model_progress(user: User, model_id: int, time: int, title: str) -> int:
    """
    Запись времени работы над моделью
    :param user:
    :param model_id:
    :param time:
    :param title:
    :return:
    """
    model = Model.objects.filter(id=model_id, user=user).first()
    progress = ModelProgress(model=model,
                             status=model.status,
                             time=time,
                             title=title,
                             datetime=timezone.now())
    progress.save()
    return progress.id


@sync_to_async
def save_image_to_progress(user: User, model_id: int, model_progress_id: int, image_file):
    model = None
    model_progress = None
    if model_id:
        model = Model.objects.get(id=model_id, user=user)

    if model_progress_id:
        model_progress = ModelProgress.objects.get(id=model_progress_id, model__user=user)
        model = model_progress.model

    image = ModelImage(image=image_file, progress=model_progress, model=model)
    image.save()


def run_telebot():
    application = ApplicationBuilder().token(TOKEN).build()
    start_handler = CommandHandler('start', start_command)
    application.add_handler(start_handler)

    help_handler = CommandHandler('help', help_command)
    application.add_handler(help_handler)

    models_handler = CommandHandler('list_models', list_models_command)
    application.add_handler(models_handler)

    list_progress_handler = CommandHandler('list_progress', list_progress_command)
    application.add_handler(list_progress_handler)

    progress_handler = CommandHandler('progress', progress_command)
    application.add_handler(progress_handler)

    progress_photo_handler = CommandHandler('progress_photo', progress_photo_command)
    application.add_handler(progress_photo_handler)

    model_photo_handler = CommandHandler('model_photo', model_photo_command)
    application.add_handler(model_photo_handler)

    image_handler = MessageHandler(filters.PHOTO, upload_photo)  # | filters.Document.JPG | filters.Document.IMAGE,
    application.add_handler(image_handler)

    application.run_polling()


if __name__ == '__main__':
    run_telebot()
