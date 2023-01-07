from django.core.management.base import BaseCommand, CommandError

from work_in_progress.telebot.main import run_telebot


class Command(BaseCommand):
    help = "Запуск телеграм бота"

    def add_arguments(self, parser):
        return

    def handle(self, *args, **options):
        try:
            run_telebot()
        except Exception as exception:
            raise CommandError(exception.args)
