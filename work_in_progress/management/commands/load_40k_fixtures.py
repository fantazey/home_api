from django.core.management.base import BaseCommand, CommandError

from work_in_progress.battlescribe.w40k import main


class Command(BaseCommand):
    help = "Загрузить фикстуры BS для 40k"

    def add_arguments(self, parser):
        return

    def handle(self, *args, **options):
        try:
            main()
        except Exception as exception:
            raise CommandError(exception.args)
