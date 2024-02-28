from functools import wraps
import html
import io
import json
import re
import traceback

from django.contrib.auth.models import User
from django.core.files.images import ImageFile
from telegram import Update, InlineKeyboardButton, InlineKeyboardMarkup
from telegram.ext import ContextTypes

from .model_tools import get_user, update_model_status, get_model, get_user_models_paged, record_model_progress, \
    save_image_to_progress, create_model, want_model, delete_model, get_last_model_progress, delete_progress
from work_in_progress.models import Model
from work_in_progress.templatetags.wip_filters import duration
from hangar import set_light_value


PARSE_MODE = 'MarkdownV2'


def require_user(func):
    @wraps(func)
    async def wrapper(update: Update, *args, **kwargs):
        user = await get_user(update.effective_chat.username)
        return await func(update, *args, user=user, **kwargs)

    return wrapper


def require_admin(func):
    @wraps(func)
    @require_user
    async def wrapper(update: Update, *args, user: User = None, **kwargs):
        if user.username != 'andy':
            raise
        return await func(update, *args, user=user, **kwargs)

    return wrapper


def require_model(func):
    @wraps(func)
    @require_user
    async def wrapper(update: Update, context: ContextTypes.DEFAULT_TYPE, *args, user: User = None, **kwargs):
        model: dict = await get_model(user, context.user_data['model_id'])
        return await func(update, context, *args, user=user, model=model, **kwargs)

    return wrapper


MAIN_KBD_LAYOUT = [
    [InlineKeyboardButton("Текущая модель", callback_data="model")],
    [InlineKeyboardButton("Записать время", callback_data="progress_add")],
    [InlineKeyboardButton("Добавить картинку", callback_data="image_add")],
    [InlineKeyboardButton("Список моделей", callback_data="model_page_0")],
    [InlineKeyboardButton("Добавить модель", callback_data="model_add")],
]


@require_user
async def start_handler(update: Update, context: ContextTypes.DEFAULT_TYPE, user: User = None):
    print(user.username)
    reply_markup = InlineKeyboardMarkup(MAIN_KBD_LAYOUT)
    if update.message:
        await update.message.reply_text("Доступные действия", reply_markup=reply_markup)
        return
    await context.bot.send_message(chat_id=update.effective_chat.id, text="Доступные действия",
                                   reply_markup=reply_markup)


async def model_keyboard_handler(update: Update, context: ContextTypes.DEFAULT_TYPE):
    query = update.callback_query
    chat_id = update.effective_chat.id
    await query.answer()
    if query.data.startswith("model_page_"):
        context.user_data['model_page'] = int(query.data.replace("model_page_", ""))
        return await handler_list_models_paged(update, context)

    if query.data.startswith("model_view_"):
        context.user_data['model_id'] = int(query.data.replace("model_view_", ""))
        return await handler_model_menu(update, context)

    if "model" == query.data:
        await handler_model_menu(update, context)
        return

    if "model_add" == query.data:
        text = "Чтобы добавить купленную модель отправь сообщение \"купил [название модели]\" или " \
               "\"хочу [название модели]\" чтобы добавить ее в вишлист"
        await context.bot.send_message(chat_id=chat_id, text=text, parse_mode=PARSE_MODE)
        return

    if "model_change_status_menu" == query.data:
        await handler_model_change_status_menu(update, context)
        return

    if query.data.startswith("model_change_status_"):
        status = query.data.replace("model_change_status_", "")
        await handler_model_change_status(update, context, status=status)
        return

    if "model_delete_menu" == query.data:
        await handler_model_delete_menu(update, context)
        return

    if "model_delete" == query.data:
        await handler_model_delete(update, context)
        return

    await start_handler(update, context)


@require_user
async def progress_keyboard_handler(update: Update, context: ContextTypes.DEFAULT_TYPE, user: User = None):
    query = update.callback_query
    chat_id = update.effective_chat.id
    await query.answer()
    if "progress_add" == query.data:
        if 'model_id' not in context.user_data or context.user_data['model_id'] is None:
            text = "Текущая модель не выбрана. Выбери модель из списка"
            await context.bot.send_message(chat_id=chat_id, text=''.join(text), parse_mode=PARSE_MODE)
            return
        model = await get_model(user, context.user_data['model_id'])
        text = f"Чтобы записать время для _{model['name']}_ отправь сообщение \"время [описание]\" " \
               f"например *1ч15м красил пушку*"
        await context.bot.send_message(chat_id=chat_id, text=''.join(text), parse_mode=PARSE_MODE)
        return

    if "progress_delete_last_menu" == query.data:
        await handler_progress_delete_last_menu(update, context)
        return

    if "progress_delete_last" == query.data:
        await handler_progress_delete_last(update, context)
        return

    await start_handler(update, context)


@require_user
async def keyboard_handler(update: Update, context: ContextTypes.DEFAULT_TYPE, user: User = None):
    query = update.callback_query
    chat_id = update.effective_chat.id
    await query.answer()
    if "image_add" == query.data:
        if 'model_id' not in context.user_data or context.user_data['model_id'] is None:
            text = "Текущая модель не выбрана. Выбери модель из списка"
            await context.bot.send_message(chat_id=chat_id, text=''.join(text), parse_mode=PARSE_MODE)
            return
        model = await get_model(user, context.user_data['model_id'])
        text = f"Чтобы добавить картинку для _{model['name']}_ отправь фото"
        await context.bot.send_message(chat_id=chat_id, text=''.join(text), parse_mode=PARSE_MODE)
        return
    await start_handler(update, context)


@require_user
async def handler_list_models_paged(update: Update, context: ContextTypes.DEFAULT_TYPE, user: User = None):
    page = context.user_data['model_page'] if 'model_page' in context.user_data else 0
    models = await get_user_models_paged(user, page)
    keyboard = []
    for model in models:
        button = InlineKeyboardButton(model['name'], callback_data=f"model_view_{model['id']}")
        keyboard.append([button])
    if page == 0:
        button_back = InlineKeyboardButton("<", callback_data="model_page_0")
    else:
        button_back = InlineKeyboardButton("<", callback_data=f"model_page_{page - 1}")
    button_forward = InlineKeyboardButton(">", callback_data=f"model_page_{page + 1}")
    button_start = InlineKeyboardButton("^", callback_data="start")
    keyboard.append([button_back, button_start, button_forward])
    reply_markup = InlineKeyboardMarkup(keyboard)
    await context.bot.edit_message_text(chat_id=update.effective_chat.id,
                                        message_id=update.callback_query.message.message_id,
                                        text=f"Модели на странице {page + 1}",
                                        reply_markup=reply_markup)


@require_model
async def handler_model_menu(update: Update, context: ContextTypes.DEFAULT_TYPE, model: dict = None):
    prev_page = context.user_data['model_page'] if 'model_page' in context.user_data else 0
    keyboard = [
        [InlineKeyboardButton("Записать время", callback_data="progress_add")],
        [InlineKeyboardButton("Добавить картинку", callback_data="image_add")],
        [InlineKeyboardButton("Изменить статус", callback_data="model_change_status_menu")],
        [InlineKeyboardButton("----", callback_data="model")],
        [InlineKeyboardButton("Удалить модель", callback_data="model_delete_menu")],
        [InlineKeyboardButton("Удалить прогресс", callback_data="progress_delete_last_menu")],
        [InlineKeyboardButton("----", callback_data="model")],
        [InlineKeyboardButton("Назад", callback_data=f"model_page_{prev_page}")],
    ]
    reply_markup = InlineKeyboardMarkup(keyboard)
    text = f"Операции для {model['name']}, в статусе: '{model['status']}', затрачено времени: ({model['duration']})"
    if update.callback_query is None:
        await context.bot.send_message(chat_id=update.effective_chat.id, text=text, reply_markup=reply_markup)
        return
    await context.bot.edit_message_text(chat_id=update.effective_chat.id,
                                        message_id=update.callback_query.message.message_id,
                                        text=text,
                                        reply_markup=reply_markup)


async def handler_model_change_status_menu(update: Update, context: ContextTypes.DEFAULT_TYPE):
    keyboard = []
    for (status, text) in Model.stages():
        keyboard.append([InlineKeyboardButton(text, callback_data=f"model_change_status_{status}")])
    keyboard.append([InlineKeyboardButton('^', callback_data=f"model")])
    await context.bot.edit_message_text(chat_id=update.effective_chat.id,
                                        message_id=update.callback_query.message.message_id,
                                        text="Выбери статус",
                                        reply_markup=InlineKeyboardMarkup(keyboard))


@require_user
async def handler_model_change_status(update: Update, context: ContextTypes.DEFAULT_TYPE,
                                status: str = None,
                                user: User = None):
    if status is not None:
        await update_model_status(user, context.user_data['model_id'], status)
    await handler_model_menu(update, context)


@require_model
async def handler_progress_add(update: Update, context: ContextTypes.DEFAULT_TYPE, user: User = None,
                                  model: dict = None):
    """
    Записать время в работу над моделью
    ожидаемые аргументы в context:
    1 - время в часах(десятичная часть через точку или запятую)
    2... все оставшиеся аргументы трактуются как описание
    :param model:
    :param user:
    :param update:
    :param context:
    :return:
    """
    track_time = calc_time(update.message.text)
    if track_time == 0:
        await handler_model_menu(update, context)
        return
    description = " ".join(update.message.text.split(" ")[1:])
    message = ["Записал время *%s* для модели _%s \- %s_" % (duration(track_time), model['id'], model['name'])]
    if len(description) > 0:
        message.append("C пояснением: _%s_" % description)
    model_progress_id = await record_model_progress(user, model['id'], track_time, description)
    context.user_data['progress_id'] = model_progress_id
    message.append("Для прикрепления фотографии отправь фото")
    await context.bot.send_message(chat_id=update.effective_chat.id, text="\n".join(message), parse_mode=PARSE_MODE)
    await handler_model_menu(update, context)
    return


def calc_time(data: str):
    track_time = 0
    time_data = data.split(" ")[0]
    hours = 0
    if 'ч' in time_data:
        hours = int(time_data.split('ч')[0])
        time_data = "".join(time_data.split('ч')[1:])
    if 'м' in time_data:
        minutes = int(time_data.split('м')[0])
        if minutes > 60:
            hours += minutes // 60
            minutes = minutes % 60

        track_time = float(hours) + (float(minutes) / 60)
    return track_time


@require_user
async def handler_image_add(update: Update, context: ContextTypes.DEFAULT_TYPE, user=None):
    """
    Сохранение фото в базу
    :param user:
    :param update:
    :param context:
    :return:
    """
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

    file_id = None
    if update.message.document:
        document = update.message.document
        file_id = document.file_id
    if update.message.photo:
        count = len(update.message.photo)
        file_id = update.message.photo[count - 1].file_id

    if file_id is None:
        return

    bot = update.get_bot()
    file = await bot.get_file(file_id)
    file_name = update.effective_chat.username + "_" + file_id
    buf = bytearray()
    await file.download_as_bytearray(buf)
    image_file = ImageFile(io.BytesIO(buf), name=file_name)

    await save_image_to_progress(user, model_id, model_progress_id, image_file)
    await context.bot.send_message(chat_id=update.effective_chat.id, text="Картиночка сохранена")
    await handler_model_menu(update, context)


@require_user
async def handler_model_buy(update: Update, context: ContextTypes.DEFAULT_TYPE, user: User = None):
    p = re.compile(r"купил ", flags=re.IGNORECASE)
    model_name = re.sub(p, "", update.message.text)
    model_id = await create_model(user, model_name)
    await context.bot.send_message(chat_id=update.effective_chat.id, text="Модель сохранена")
    context.user_data["model_id"] = model_id
    await handler_model_menu(update, context)


@require_user
async def handler_model_want(update: Update, context: ContextTypes.DEFAULT_TYPE, user: User = None):
    p = re.compile(r"хочу ", flags=re.IGNORECASE)
    model_name = re.sub(p, "", update.message.text)
    model_id = await want_model(user, model_name)
    await context.bot.send_message(chat_id=update.effective_chat.id, text="Модель сохранена")
    context.user_data["model_id"] = model_id
    await handler_model_menu(update, context)


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


@require_admin
async def handler_hangar_light(update: Update, context: ContextTypes.DEFAULT_TYPE):
    p = re.compile(r"^свет\s+", flags=re.IGNORECASE)
    value = re.sub(p, "", update.message.text)
    set_light_value(int(value))
    await context.bot.send_message(chat_id=update.effective_chat.id, text="Команда отправлена")


@require_model
async def handler_model_delete_menu(update: Update, context: ContextTypes.DEFAULT_TYPE, model: dict = None):
    keyboard = [
        [InlineKeyboardButton("Удалить модель", callback_data="model_delete")],
        [InlineKeyboardButton("Назад", callback_data="model")],
    ]
    reply_markup = InlineKeyboardMarkup(keyboard)
    text = f"""Удалить модель {model['name']}, все записи времени и все фотографии?"""
    if update.callback_query is None:
        await context.bot.send_message(chat_id=update.effective_chat.id, text=text, reply_markup=reply_markup)
        return
    await context.bot.edit_message_text(chat_id=update.effective_chat.id,
                                        message_id=update.callback_query.message.message_id,
                                        text=text,
                                        reply_markup=reply_markup)


@require_model
async def handler_model_delete(update: Update, context: ContextTypes.DEFAULT_TYPE, user: User = None,
                               model: dict = None):
    await delete_model(user, model['id'])
    del context.user_data['model_id']
    del context.user_data['progress_id']
    await context.bot.send_message(chat_id=update.effective_chat.id, text="Модель удалена")
    await start_handler(update, context)


@require_model
async def handler_progress_delete_last_menu(update: Update, context: ContextTypes.DEFAULT_TYPE, user: User = None,
                                            model: dict = None):
    keyboard = [
        [InlineKeyboardButton("Удалить запись времени", callback_data="progress_delete_last")],
        [InlineKeyboardButton("Назад", callback_data="model")],
    ]
    record = get_last_model_progress(user, model['id'])
    context.user_data['progress_id'] = record['id']
    reply_markup = InlineKeyboardMarkup(keyboard)
    text = f"""Удалить запись времени {record['description']} {duration(record['time'])} от {record['datetime']}
 и связанные фотографии?"""
    if update.callback_query is None:
        await context.bot.send_message(chat_id=update.effective_chat.id, text=text, reply_markup=reply_markup)
        return
    await context.bot.edit_message_text(chat_id=update.effective_chat.id,
                                        message_id=update.callback_query.message.message_id,
                                        text=text,
                                        reply_markup=reply_markup)


@require_user
async def handler_progress_delete_last(update: Update, context: ContextTypes.DEFAULT_TYPE, user: User = None):
    await delete_progress(user, context.user_data['model_id'], context.user_data['progress_id'])
    del context.user_data['progress_id']
    await context.bot.send_message(chat_id=update.effective_chat.id, text="Модель удалена")
    await start_handler(update, context)


async def handler_hangar_menu(update: Update, context: ContextTypes.DEFAULT_TYPE):
    pass