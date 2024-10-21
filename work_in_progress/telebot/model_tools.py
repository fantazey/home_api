import datetime

from asgiref.sync import sync_to_async
from django.contrib.auth.models import User
from django.db.models import Max
from django.utils import timezone

from work_in_progress.models import Model, ModelProgress, ModelImage, Artist, UserModelStatus
from work_in_progress.templatetags.wip_filters import duration


@sync_to_async
def update_model_status(user: User, model_id: int, status: str) -> None:
    model = Model.objects.get(id=model_id, user=user)
    model.change_status(status)


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
def get_model(user: User, model_id: int) -> dict:
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
        'status': model.user_status.name,
        'duration': duration(model.get_hours_spent),
        'model': model
    }


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
    olddate = timezone.now() - datetime.timedelta(days=2000)
    models = Model.objects.filter(user=user)\
        .annotate(max_date=Max('progress__datetime', default=olddate))\
        .order_by('-max_date')[slice_start:slice_end]
    result = []
    for model in models:
        result.append({
            'id': model.id,
            'name': model.name,
            'status': model.user_status.name
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
                             user_status=model.user_status,
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
    status = UserModelStatus.objects.get(user=user, is_initial=True)
    model = Model(name=name, user=user, user_status=status)
    model.save()
    return model.id


@sync_to_async
def delete_model(user: User, model_id: int):
    model = Model.objects.get(id=model_id, user=user)
    images = ModelImage.objects.filter(model=model)
    images.delete()
    progress = ModelProgress.objects.filter(model=model)
    progress.delete()
    model.delete()


@sync_to_async
def get_last_model_progress(user: User, model_id: int) -> dict:
    """
    Получить последнюю запись времени по модели
    :param user:
    :param model_id:
    :return:
    """
    model = Model.objects.get(id=model_id, user=user)
    progress = ModelProgress.objects.filter(model__user=user, model_id=model_id).order_by('id').last()
    if progress is not None:
        return {
            'id': progress.id,
            'description': progress.description,
            'status': progress.user_status.name,
            'time': progress.time,
            'datetime': progress.datetime.strftime("%d-%m-%Y %H:%M:%S"),
            'model': model
        }
    return {

    }


@sync_to_async
def delete_progress(user: User, model_id: int, progress_id: int):
    model = Model.objects.get(id=model_id, user=user)
    progress = ModelProgress.objects.get(id=progress_id, model=model)
    images = ModelImage.objects.filter(progress=progress)
    images.update(progress=None)
    progress.delete()


@sync_to_async
def get_status_list(user: User):
    return [(x.slug, x.name) for x in UserModelStatus.objects.filter(user=user)]
