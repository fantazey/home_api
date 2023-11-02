"""
Бот для записи времени по покрасу через телеграм
необходимый функционал:
- записать время
- сохранить фотку в запись времени
- сохранить фотку в модель
- обновить запись времени
- удалить запись времени
"""
import datetime
import html
import io
import logging
import re
import traceback
import json

from asgiref.sync import sync_to_async
from django.db.models import Max
from django.utils import timezone
from django.core.files.images import ImageFile
from django.contrib.auth.models import User
from telegram import Update, InlineKeyboardButton, InlineKeyboardMarkup
from telegram.ext import ApplicationBuilder, CommandHandler, ContextTypes, MessageHandler, filters, \
    CallbackQueryHandler

from home_api.private_settings import TOKEN
from work_in_progress.templatetags.wip_filters import duration
from work_in_progress.models import Model, ModelProgress, ModelImage, Artist

CHAT_PROGRESS_RECORDS_FOR_PHOTO = {}
CHAT_MODEL_RECORDS_FOR_PHOTO = {}
CHAT_PROGRESS_RECORDS = {}
PARSE_MODE = 'MarkdownV2'

TIME_MATCHER = re.compile(r'((?P<hours>\d+)ч)?((?P<minutes>\d+)м)?(?P<description>.*)')

logging.basicConfig(
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s',
    level=logging.DEBUG
)

MAIN_KBD_LAYOUT = [
    [InlineKeyboardButton("Текущая модель", callback_data="model")],
    [InlineKeyboardButton("Записать время", callback_data="add_progress")],
    [InlineKeyboardButton("Добавить картинку", callback_data="add_image")],
    [InlineKeyboardButton("Список моделей", callback_data="page_0")],
    [InlineKeyboardButton("Добавить модель", callback_data="add_model")],
]


async def start_command(update: Update, context: ContextTypes.DEFAULT_TYPE):
    await get_user(update.effective_chat.username)
    reply_markup = InlineKeyboardMarkup(MAIN_KBD_LAYOUT)
    if update.message:
        await update.message.reply_text("Доступные действия", reply_markup=reply_markup)
        return
    await context.bot.send_message(chat_id=update.effective_chat.id, text="Доступные действия",
                                   reply_markup=reply_markup)


async def keyboard_handler(update: Update, context: ContextTypes.DEFAULT_TYPE):
    user = await get_user(update.effective_chat.username)
    query = update.callback_query
    chat_id = update.effective_chat.id
    await query.answer()
    if "start" == query.data:
        reply_markup = InlineKeyboardMarkup(MAIN_KBD_LAYOUT)
        await context.bot.edit_message_text(chat_id=chat_id,
                                            message_id=update.callback_query.message.message_id,
                                            text="Доступные действия",
                                            reply_markup=reply_markup)
        return

    if re.search("^page_\d+$", query.data):
        page = int(query.data.replace("page_", ""))
        await handle_list_models_paged(page, update, context)
        return

    if re.search("^model_\d+$", query.data):
        context.user_data['model_id'] = int(query.data.replace("model_", ""))
        await handle_model_actions(update, context)
        return

    if "model" == query.data:
        await handle_model_actions(update, context)
        return

    if "add_progress" == query.data:
        model = await get_model_dict(user, context.user_data['model_id'])
        text = ['Чтобы записать время для _',
                model['name'],
                '_ отправь сообщение \"время [описание]\"',
                'например *1ч15м покрасил пушку*']
        await context.bot.send_message(chat_id=chat_id, text=''.join(text), parse_mode=PARSE_MODE)
        return

    if "add_image" == query.data:
        model = await get_model_dict(user, context.user_data['model_id'])
        text = ['Чтобы добавить картинку для _',
                model['name'],
                '_ отправь фото']
        await context.bot.send_message(chat_id=chat_id, text=''.join(text), parse_mode=PARSE_MODE)
        return

    if "add_model" == query.data:
        text = f"Чтобы добавить модель отправь сообщение \"купил [название модели]\""
        await context.bot.send_message(chat_id=chat_id, text=text, parse_mode=PARSE_MODE)
        return

    if "change_status" == query.data:
        await handler_change_status(update, context)
        return

    if re.match("^change_status_.*$", query.data):
        status = query.data.replace("change_status_", "")
        await handle_update_status(status, update, context)
        return

    await start_command(update, context)


async def handler_change_status(update: Update, context: ContextTypes.DEFAULT_TYPE):
    keyboard = []
    for (status, text) in Model.stages():
        keyboard.append([InlineKeyboardButton(text, callback_data=f"change_status_{status}")])
    keyboard.append([InlineKeyboardButton('^', callback_data=f"model")])
    await context.bot.edit_message_text(chat_id=update.effective_chat.id,
                                        message_id=update.callback_query.message.message_id,
                                        text="Выбери статус",
                                        reply_markup=InlineKeyboardMarkup(keyboard))


async def handle_update_status(status: str, update: Update, context: ContextTypes.DEFAULT_TYPE):
    model_id = context.user_data['model_id']
    user = await get_user(update.effective_chat.username)
    await update_model_status(user, model_id, status)
    await handle_model_actions(update, context)


async def handle_list_models_paged(page: int, update: Update, context: ContextTypes.DEFAULT_TYPE):
    user = await get_user(update.effective_chat.username)
    models = await get_user_models_paged(user, page)
    context.user_data['page'] = page
    keyboard = []
    for model in models:
        button = InlineKeyboardButton(model['name'], callback_data=f"model_{model['id']}")
        keyboard.append([button])
    if page == 0:
        button_back = InlineKeyboardButton("<", callback_data="page_0")
    else:
        button_back = InlineKeyboardButton("<", callback_data=f"page_{page - 1}")
    button_forward = InlineKeyboardButton(">", callback_data=f"page_{page + 1}")
    button_start = InlineKeyboardButton("^", callback_data="start")
    keyboard.append([button_back, button_start, button_forward])
    reply_markup = InlineKeyboardMarkup(keyboard)
    await context.bot.edit_message_text(chat_id=update.effective_chat.id,
                                        message_id=update.callback_query.message.message_id,
                                        text=f"Модели на странице {page + 1}",
                                        reply_markup=reply_markup)


async def handle_model_actions(update: Update, context: ContextTypes.DEFAULT_TYPE):
    model_id = context.user_data['model_id']
    user = await get_user(update.effective_chat.username)
    model: dict = await get_model_dict(user, model_id)
    prev_page = context.user_data['page'] if 'page' in context.user_data else 0
    keyboard = [
        [InlineKeyboardButton("Записать время", callback_data="add_progress")],
        [InlineKeyboardButton("Добавить картинку", callback_data="add_image")],
        [InlineKeyboardButton("Изменить статус", callback_data="change_status")],
        [InlineKeyboardButton("Назад", callback_data=f"page_{prev_page}")],
    ]
    reply_markup = InlineKeyboardMarkup(keyboard)
    text = f"""    
Операции для {model['name']}
в статусе: '{model['status']}' 
затрачено времени: ({model['duration']})
    """
    if update.callback_query is None:
        await context.bot.send_message(chat_id=update.effective_chat.id, text=text, reply_markup=reply_markup)
        return
    await context.bot.edit_message_text(chat_id=update.effective_chat.id,
                                        message_id=update.callback_query.message.message_id,
                                        text=text,
                                        reply_markup=reply_markup)


async def progress_command(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """
    Записать время в работу над моделью
    ожидаемые аргументы в context:
    1 - время в часах(десятичная часть через точку или запятую)
    2... все оставшиеся аргументы трактуются как описание
    :param update:
    :param context:
    :return:
    """
    model_id = context.user_data['model_id']
    description = ""
    track_time = 0
    res = TIME_MATCHER.match(update.message.text)
    if len(res.groups()) > 0:
        track_time = float(res.group("hours") or 0) + (float(res.group("minutes") or 0) / 60)
        description = res.group("description")
    if track_time == 0:
        return
    user = await get_user(update.effective_chat.username)
    model = await get_model(user, model_id)
    message = ["Записал время *%s* для модели _%s \- %s_" % (duration(track_time), model.id, model.name)]
    if len(description) > 0:
        message.append("C пояснением: _%s_" % description)
    model_progress_id = await record_model_progress(user, model_id, track_time, description)
    context.user_data['progress_id'] = model_progress_id
    message.append("Для прикрепления фотографии отправь фото")
    await context.bot.send_message(chat_id=update.effective_chat.id, text="\n".join(message), parse_mode='MarkdownV2')
    await handle_model_actions(update, context)
    return


async def upload_photo(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """
    Сохранение фото в базу
    :param update:
    :param context:
    :return:
    """
    user = await get_user(update.effective_chat.username)
    is_progress_photo = 'progress_id' in context.user_data
    is_model_photo = 'model_id' in context.user_data

    if not is_progress_photo and not is_model_photo:
        return
    if not update.message.document and not update.message.photo:
        return

    model_progress_id = model_id = None

    if is_progress_photo:
        model_progress_id = context.user_data['progress_id']
    if is_model_photo:
        model_id = context.user_data['model_id']

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
        return

    file = await bot.get_file(file_id)
    file_name = update.effective_chat.username + "_" + file_id
    await file.download_as_bytearray(buf)
    image_file = ImageFile(io.BytesIO(buf), name=file_name)
    await save_image_to_progress(user, model_id, model_progress_id, image_file)
    await context.bot.send_message(chat_id=update.effective_chat.id, text="Картиночка сохранена")
    await handle_model_actions(update, context)


async def add_model_handler(update: Update, context: ContextTypes.DEFAULT_TYPE):
    model_name = update.message.text.replace("купил ", "")
    user = await get_user(update.effective_chat.username)
    model_id = await create_model(user, model_name)
    await get_model_dict(user, model_id)
    await context.bot.send_message(chat_id=update.effective_chat.id, text="Модель сохранена")
    context.user_data["model_id"] = model_id
    await handle_model_actions(update, context)


async def error_handler(update: Update, context: ContextTypes.DEFAULT_TYPE):
    tb_list = traceback.format_exception(None, context.error, context.error.__traceback__)
    tb_string = "".join(tb_list)
    update_str = update.to_dict() if isinstance(update, Update) else str(update)
    message = html.escape(
        "An exception was raised while handling an update\n"
        f"update = {json.dumps(update_str, indent=2, ensure_ascii=False)}"
        "\n\n"
        f"context.chat_data = {str(context.chat_data)}\n\n"
        f"context.user_data = {str(context.user_data)}\n\n"
        f"{tb_string}"
    )
    await context.bot.send_message(
        chat_id=update.effective_chat.id, text=message, parse_mode=PARSE_MODE
    )


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
def get_user_models_paged(user: User, page: int) -> list[dict]:
    """
    Получить список последних 5 моделей в работе
    :param page:
    :param user:
    :return:
    """
    slice_start = page * 5
    slice_end = (page + 1) * 5
    models = Model.objects.annotate(
        last_record=Max('modelprogress__datetime')
    ).filter(user=user).order_by('-last_record')[slice_start:slice_end]
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
def get_model_dict(user: User, model_id: int) -> dict:
    """
    Получить модель по ид
    :param user:
    :param model_id:
    :return:
    """
    model = Model.objects.get(id=model_id, user=user)
    return {
        'id': model.id,
        'name': model.name,
        'status': model.get_status_display(),
        'duration': duration(model.get_hours_spent),
        'model': model
    }


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


@sync_to_async
def create_model(user: User, name: str) -> int:
    model = Model(name=name, user=user, status=Model.Status.IN_INVENTORY, buy_date=datetime.datetime.now())
    model.save()
    return model.id


@sync_to_async
def update_model_status(user: User, model_id: int, status: str) -> None:
    model = Model.objects.get(id=model_id, user=user)
    model.change_status(status)


def run_telebot():
    #bot_token = TEST_TOKEN if DEBUG else TOKEN
    application = ApplicationBuilder().token(TOKEN).build()
    application.add_handler(CommandHandler('start', start_command))
    application.add_handler(MessageHandler(filters.PHOTO, upload_photo))
    application.add_handler(CallbackQueryHandler(keyboard_handler))
    application.add_handler(MessageHandler(filters.Regex("^\d+ч|\d+м/"), progress_command))
    application.add_handler(MessageHandler(filters.Regex("^купил .*"), add_model_handler))
    application.add_error_handler(error_handler)

    application.run_polling()


if __name__ == '__main__':
    run_telebot()
