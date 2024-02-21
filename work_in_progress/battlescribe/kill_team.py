from os import walk
from os import path

from bs4 import BeautifulSoup
from work_in_progress.models import KillTeam, Operative

SOURCE_PATH = path.join(path.dirname(path.abspath(__file__)), 'fixtures', 'kill-team')


def main():
    """
    Читаем фикстуры скачанные с https://github.com/BSData/wh40k-killteam
    сохраняем пока только часть данных себе в базу
    """
    for root, dirs, files in walk(SOURCE_PATH):
        for file in files:
            if file.startswith("2021") and file.endswith(".cat"):
                print('read:', file)
                read_fixture_file(path.join(root, file))


def read_fixture_file(source):
    """
    Читаем
    :param source:
    :return:
    """
    with open(source, 'r') as f:
        s = f.readlines()
        soup = BeautifulSoup("".join(s), "xml")
    kt_name = soup.find('catalogue').attrs['name']
    kt, created = KillTeam.objects.get_or_create(name=kt_name)
    operatives = soup.find_all('selectionEntry', {'type': 'model'})
    for entry in operatives:
        name = entry.attrs['name']
        if not Operative.objects.filter(name=name, kill_team=kt).exists():
            unit = Operative(name=name, kill_team=kt)
            unit.save()