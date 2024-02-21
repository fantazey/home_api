from django.core.management.base import BaseCommand, CommandError

from work_in_progress.battlescribe.kill_team import main


class Command(BaseCommand):
    help = "Загрузить фикстуры BS для KT"

    def add_arguments(self, parser):
        return

    def handle(self, *args, **options):
        try:
            print("start")
            main()
        except Exception as exception:
            raise CommandError(exception.args)
