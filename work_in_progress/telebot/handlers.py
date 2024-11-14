from functools import wraps
import io
import re

from django.contrib.auth.models import User
from django.core.files.images import ImageFile
from telegram import Update, InlineKeyboardButton, InlineKeyboardMarkup
from telegram.constants import ParseMode
from telegram.ext import ContextTypes

from .model_tools import get_user, update_model_status, get_model, get_user_models_paged, record_model_progress, \
    save_image_to_progress, create_model, delete_model, get_last_model_progress, delete_progress, \
    get_status_list
from work_in_progress.templatetags.wip_filters import duration
from .hangar import set_light_value, set_light_full, set_light_low, set_light_mid, set_light_off, set_light_fade, \
    set_painted_count, set_unpainted_count, display_show_all, display_show_painted, display_show_unpainted, sync_time, \
    display_show_time, display_show_date, set_light_fixed


PARSE_MODE = ParseMode.MARKDOWN_V2

ADD_MODEL = f"Чтобы добавить купленную модель отправь сообщение \"купил [название модели]\" или" \
            f" \"хочу [название модели]\" чтобы добавить ее в вишлист"

ADD_IMAGE = f"Чтобы добавить картинку для модели, выбери модель в списке и отправь фото в чат"

ADD_PROGRESS = f"Чтобы записать время для модели, выбери модель в списке и отправь сообщение \"время [описание]\" " \
               f"например *1ч15м красил пушку*"

RULES = [
    ADD_MODEL,
    ADD_PROGRESS,
    ADD_IMAGE
]

BASE_MAIN_KBD_LAYOUT = [
    [InlineKeyboardButton("Список моделей", callback_data="model_page_0")],
]

MAIN_KBD_LAYOUT = [
    [InlineKeyboardButton("Текущая модель", callback_data="model")],
    [InlineKeyboardButton("Список моделей", callback_data="model_page_0")],
]

ADMIN_MAIN_KBD_LAYOUT = [
    [InlineKeyboardButton("Текущая модель", callback_data="model")],
    [InlineKeyboardButton("Список моделей", callback_data="model_page_0")],
    [InlineKeyboardButton("Дисплей", callback_data="hangar_display_menu")],
    [InlineKeyboardButton("Свет", callback_data="hangar_light_menu")],
    [InlineKeyboardButton("Обновить время", callback_data="hangar_set_time")]
]

HANGAR_DISPLAY_KBD_LAYOUT = [
    [InlineKeyboardButton("Сброс", callback_data="hangar_display_mode_reset")],
    [InlineKeyboardButton("Дата", callback_data="hangar_display_mode_date")],
    [InlineKeyboardButton("Время", callback_data="hangar_display_mode_time")],
    [InlineKeyboardButton("Покрас", callback_data="hangar_display_mode_painted")],
    [InlineKeyboardButton("Непокрас", callback_data="hangar_display_mode_unpainted")],
    [InlineKeyboardButton("^", callback_data="start")]
]

HANGAR_LIGHT_KBD_LAYOUT = [
    [InlineKeyboardButton("Выключить", callback_data="hangar_light_mode_off")],
    [InlineKeyboardButton("Мигающий", callback_data="hangar_light_mode_fade")],
    [InlineKeyboardButton("Фиксированный", callback_data="hangar_light_mode_fixed")],
    [InlineKeyboardButton("Низкий", callback_data="hangar_light_mode_low")],
    [InlineKeyboardButton("Средний", callback_data="hangar_light_mode_mid")],
    [InlineKeyboardButton("Полный", callback_data="hangar_light_mode_high")],
    [InlineKeyboardButton("^", callback_data="start")]
]


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


def can_edit_message(update: Update, markup: InlineKeyboardMarkup):
    return update.callback_query is not None and update.callback_query.message.reply_markup != markup


@require_user
async def start_handler(update: Update, context: ContextTypes.DEFAULT_TYPE, user: User, **kwargs):
    kbd = BASE_MAIN_KBD_LAYOUT
    if 'model_id' in context.user_data and context.user_data['model_id'] is not None:
        kbd = MAIN_KBD_LAYOUT
    if user.username == 'andy':
        kbd = ADMIN_MAIN_KBD_LAYOUT
    reply_markup = InlineKeyboardMarkup(kbd)
    text = "\n\n".join(RULES)
    await send_markup(update, context, reply_markup, text)
    return


async def model_keyboard_handler(update: Update, context: ContextTypes.DEFAULT_TYPE):
    query = update.callback_query
    await query.answer()
    if query.data.startswith("model_page_"):
        context.user_data['model_page'] = int(query.data.replace("model_page_", ""))
        return await handler_list_models_paged(update, context)

    if query.data.startswith("model_view_"):
        model_id = int(query.data.replace("model_view_", ""))
        if 'model_id' in context.user_data and model_id != context.user_data['model_id'] and \
                'progress_id' in context.user_data:
            # нужно сбрасывать ид записи времени при переключении модели,чтобы при загрузке фотографий они
            # грузились в новую выбранную модель, а не в прогресс который был записан для другой модели
            del context.user_data['progress_id']
        context.user_data['model_id'] = model_id
        return await handler_model_menu(update, context)

    if "model" == query.data:
        if 'model_id' not in context.user_data or context.user_data['model_id'] is None:
            return
        await handler_model_menu(update, context)
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


@require_user
async def progress_keyboard_handler(update: Update, context: ContextTypes.DEFAULT_TYPE, user: User = None):
    if 'model_id' not in context.user_data or context.user_data['model_id'] is None:
        return
    query = update.callback_query
    await query.answer()
    if "progress_delete_last_menu" == query.data:
        await handler_progress_delete_last_menu(update, context)
        return

    if "progress_delete_last" == query.data:
        await handler_progress_delete_last(update, context)
        return

    await start_handler(update, context)


@require_user
async def keyboard_handler(update: Update, context: ContextTypes.DEFAULT_TYPE, **kwargs):
    query = update.callback_query
    chat_id = update.effective_chat.id
    await query.answer()
    if "image_add" == query.data:
        if 'model_id' not in context.user_data or context.user_data['model_id'] is None:
            text = "Выбери модель из списка"
            await context.bot.send_message(chat_id=chat_id, text=text, parse_mode=PARSE_MODE)
        return
    return await start_handler(update, context)


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
    text = f"Модели на странице {page + 1}"
    await send_markup(update, context, reply_markup, text)
    return


@require_model
async def handler_model_menu(update: Update, context: ContextTypes.DEFAULT_TYPE, model: dict = None, **kwargs):
    prev_page = context.user_data['model_page'] if 'model_page' in context.user_data else 0
    keyboard = [
        [InlineKeyboardButton("Изменить статус", callback_data="model_change_status_menu")],
        [InlineKeyboardButton("----", callback_data="model")],
        [InlineKeyboardButton("Удалить модель", callback_data="model_delete_menu")],
        [InlineKeyboardButton("Удалить прогресс", callback_data="progress_delete_last_menu")],
        [InlineKeyboardButton("----", callback_data="model")],
        [InlineKeyboardButton("Назад", callback_data=f"model_page_{prev_page}")],
    ]
    reply_markup = InlineKeyboardMarkup(keyboard)
    text = f"Операции для {model['name']}, в статусе: '{model['status']}', затрачено времени: ({model['duration']})"
    await send_markup(update, context, reply_markup, text)
    return


@require_user
async def handler_model_change_status_menu(update: Update, context: ContextTypes.DEFAULT_TYPE, user: User):
    keyboard = []
    statuses = await get_status_list(user)
    for (status, text) in statuses:
        keyboard.append([InlineKeyboardButton(text, callback_data=f"model_change_status_{status}")])
    keyboard.append([InlineKeyboardButton('^', callback_data=f"model")])
    reply_markup = InlineKeyboardMarkup(keyboard)
    text = "Выбери статус"
    await send_markup(update, context, reply_markup, text)
    return


@require_user
async def handler_model_change_status(update: Update, context: ContextTypes.DEFAULT_TYPE, status: str = None,
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
    print("Track time {}".format(track_time))
    if track_time == 0:
        await handler_model_menu(update, context)
        return
    description = " ".join(update.message.text.split(" ")[1:])
    print("Track description \"{}\"".format(description))
    message = ["Записал время *%s* для модели _%s \- %s_" % (duration(track_time), model['id'], model['name'])]
    if len(description) > 0:
        message.append("C пояснением: _%s_" % description)
    model_progress_id = await record_model_progress(user, model['id'], track_time, description)
    context.user_data['progress_id'] = model_progress_id
    message.append("Для прикрепления фотографии отправь фото")
    text = "\n".join(message)
    await context.bot.send_message(chat_id=update.effective_chat.id, text=text, parse_mode=PARSE_MODE)
    await handler_model_menu(update, context)
    return


def calc_time(data: str):
    time_data = data.split(" ")[0]
    print("Time data {}".format(time_data))
    hours = 0
    minutes = 0
    if 'ч' in time_data:
        hours = int(time_data.split('ч')[0])
        print("Read hours {}".format(hours))
        time_data = "".join(time_data.split('ч')[1:])
        print("Left time data {}".format(time_data))
    if 'м' in time_data:
        minutes = int(time_data.split('м')[0])
        print("Read minuted {}".format(minutes))
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
    file_id = None

    if update.message.document:
        document = update.message.document
        file_id = document.file_id

    if update.message.photo:
        count = len(update.message.photo)
        file_id = update.message.photo[count - 1].file_id

    if file_id is None:
        return

    model_progress_id = model_id = None
    if 'progress_id' in context.user_data:
        model_progress_id = context.user_data['progress_id']

    if 'model_id' in context.user_data:
        model_id = context.user_data['model_id']

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
    model_id = await create_model(user, model_name)
    await context.bot.send_message(chat_id=update.effective_chat.id, text="Модель сохранена")
    context.user_data["model_id"] = model_id
    await handler_model_menu(update, context)


@require_model
async def handler_model_delete_menu(update: Update, context: ContextTypes.DEFAULT_TYPE, model: dict = None,
                                    **kwargs):
    keyboard = [
        [InlineKeyboardButton("Удалить модель", callback_data="model_delete")],
        [InlineKeyboardButton("Назад", callback_data="model")],
    ]
    reply_markup = InlineKeyboardMarkup(keyboard)
    text = f"""Удалить модель {model['name']}, все записи времени и все фотографии?"""
    await send_markup(update, context, reply_markup, text)
    return


@require_model
async def handler_model_delete(update: Update, context: ContextTypes.DEFAULT_TYPE, user: User = None,
                               model: dict = None):
    await delete_model(user, model['id'])
    del context.user_data['model_id']
    if 'progress_id' in context.user_data:
        del context.user_data['progress_id']
    await context.bot.send_message(chat_id=update.effective_chat.id, text="Модель удалена")
    return await start_handler(update, context)


@require_model
async def handler_progress_delete_last_menu(update: Update, context: ContextTypes.DEFAULT_TYPE, user: User = None,
                                            model: dict = None):
    keyboard = [
        [InlineKeyboardButton("Удалить запись времени", callback_data="progress_delete_last")],
        [InlineKeyboardButton("Назад", callback_data="model")],
    ]
    record = await get_last_model_progress(user, model['id'])
    if 'id' not in record:
        return
    context.user_data['progress_id'] = record['id']
    reply_markup = InlineKeyboardMarkup(keyboard)
    text = f"""Удалить запись времени {record['description']} {duration(record['time'])} от {record['datetime']}
 и связанные фотографии?"""
    await send_markup(update, context, reply_markup, text)
    return


@require_user
async def handler_progress_delete_last(update: Update, context: ContextTypes.DEFAULT_TYPE, user: User = None):
    await delete_progress(user, context.user_data['model_id'], context.user_data['progress_id'])
    del context.user_data['progress_id']
    await context.bot.send_message(chat_id=update.effective_chat.id, text="Запись времени удалена")
    await start_handler(update, context)


async def error_handler(update: Update, context: ContextTypes.DEFAULT_TYPE):
    if update is None:
        return
    print(context.error)
    print(context.error.with_traceback())
    await context.bot.send_message(chat_id=update.effective_chat.id, text="Error", parse_mode=PARSE_MODE)


@require_admin
async def handler_hangar_light(update: Update, context: ContextTypes.DEFAULT_TYPE, **kwargs):
    p = re.compile(r"^свет\s+", flags=re.IGNORECASE)
    value = re.sub(p, "", update.message.text)
    set_light_value(int(value))
    await context.bot.send_message(chat_id=update.effective_chat.id, text="Команда отправлена")


@require_admin
async def handler_hangar_painted(update: Update, context: ContextTypes.DEFAULT_TYPE, **kwargs):
    p = re.compile(r"^покрас\s+", flags=re.IGNORECASE)
    value = re.sub(p, "", update.message.text)
    set_painted_count(int(value))
    await context.bot.send_message(chat_id=update.effective_chat.id, text="Команда отправлена")


@require_admin
async def handler_hangar_unpainted(update: Update, context: ContextTypes.DEFAULT_TYPE, **kwargs):
    p = re.compile(r"^непокрас\s+", flags=re.IGNORECASE)
    value = re.sub(p, "", update.message.text)
    set_unpainted_count(int(value))
    await context.bot.send_message(chat_id=update.effective_chat.id, text="Команда отправлена")


@require_admin
async def hangar_keyboard_handler(update: Update, context: ContextTypes.DEFAULT_TYPE, **kwargs):
    query = update.callback_query
    await query.answer()
    if "hangar_set_time" == query.data:
        return await handler_hangar_set_time(update, context)

    if "hangar_display_menu" == query.data:
        return await handler_hangar_display_menu(update, context)

    if "hangar_light_menu" == query.data:
        return await handler_hangar_light_menu(update, context)

    text = "Команда отправлена"
    if "hangar_display_mode_reset" == query.data:
        display_show_all()
        return await context.bot.send_message(chat_id=update.effective_chat.id, text=text)

    if "hangar_display_mode_date" == query.data:
        display_show_date()
        return await context.bot.send_message(chat_id=update.effective_chat.id, text=text)

    if "hangar_display_mode_time" == query.data:
        display_show_time()
        return await context.bot.send_message(chat_id=update.effective_chat.id, text=text)

    if "hangar_display_mode_painted" == query.data:
        display_show_painted()
        return await context.bot.send_message(chat_id=update.effective_chat.id, text=text)

    if "hangar_display_mode_unpainted" == query.data:
        display_show_unpainted()
        return await context.bot.send_message(chat_id=update.effective_chat.id, text=text)

    if "hangar_light_mode_off" == query.data:
        set_light_off()
        return await context.bot.send_message(chat_id=update.effective_chat.id, text=text)

    if "hangar_light_mode_fade" == query.data:
        set_light_fade()
        return await context.bot.send_message(chat_id=update.effective_chat.id, text=text)

    if "hangar_light_mode_fixed" == query.data:
        set_light_fixed()
        return await context.bot.send_message(chat_id=update.effective_chat.id, text=text)

    if "hangar_light_mode_low" == query.data:
        set_light_low()
        return await context.bot.send_message(chat_id=update.effective_chat.id, text=text)

    if "hangar_light_mode_mid" == query.data:
        set_light_mid()
        return await context.bot.send_message(chat_id=update.effective_chat.id, text=text)

    if "hangar_light_mode_high" == query.data:
        set_light_full()
        return await context.bot.send_message(chat_id=update.effective_chat.id, text=text)


@require_admin
async def handler_hangar_set_time(update: Update, context: ContextTypes.DEFAULT_TYPE, **kwargs):
    sync_time()
    await context.bot.send_message(chat_id=update.effective_chat.id, text="Команда отправлена")


@require_admin
async def handler_hangar_display_menu(update: Update, context: ContextTypes.DEFAULT_TYPE, **kwargs):
    reply_markup = InlineKeyboardMarkup(HANGAR_DISPLAY_KBD_LAYOUT)
    text = "Меню экрана ангара"
    await send_markup(update, context, reply_markup, text)
    return


@require_admin
async def handler_hangar_light_menu(update: Update, context: ContextTypes.DEFAULT_TYPE, **kwargs):
    reply_markup = InlineKeyboardMarkup(HANGAR_LIGHT_KBD_LAYOUT)
    text = "Меню подсветки ангара"
    await send_markup(update, context, reply_markup, text)
    return


async def send_markup(update: Update, context: ContextTypes.DEFAULT_TYPE, markup: InlineKeyboardMarkup, text: str):
    if update.callback_query is not None:
        if update.callback_query.message.reply_markup == markup:
            return

        await context.bot.edit_message_text(chat_id=update.effective_chat.id,
                                            message_id=update.callback_query.message.message_id,
                                            text=text,
                                            reply_markup=markup)
        return
    await context.bot.send_message(chat_id=update.effective_chat.id, text=text, reply_markup=markup)
    return
