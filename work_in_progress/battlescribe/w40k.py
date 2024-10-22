from os import walk
from os import path

from bs4 import BeautifulSoup
from work_in_progress.battlescribe.models import BSUnit, BSCategory

SOURCE_PATH = path.join(path.dirname(path.abspath(__file__)), 'fixtures', '40k')


def main():
    """
    Читаем фикстуры скачанные с https://github.com/BSData/wh40k
    сохраняем пока только часть данных себе в базу
    """
    for root, dirs, files in walk(SOURCE_PATH):
        for file in files:
            if file.endswith(".cat"):
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
        soup = BeautifulSoup("".join(s), 'xml')
    is_common = soup.find_all('gameSystem')
    if len(is_common) > 0:
        print('40k base rules gamesystem file')
        return

    units_entries = soup.find_all('selectionEntry', {'type': 'unit'})
    category_name = soup.find('catalogue').attrs['name']
    print("read catalog for:", category_name)
    category, created = BSCategory.objects.get_or_create(name=category_name)
    if created:
        category.source = source
        category.save()

    print("category: ", category, " created:", created)
    for entry in units_entries:
        name = entry.attrs['name']
        print("unit entry:", name)
        if not BSUnit.objects.filter(name=name, bs_category=category).exists():
            unit = BSUnit(name=name, bs_category=category)
            unit.save()

    model_entries = soup.find_all('selectionEntry', {'type': 'model'})
    for entry in model_entries:
        name = entry.attrs['name']
        print("unit entry:", name)
        if not BSUnit.objects.filter(name=name, bs_category=category).exists():
            unit = BSUnit(name=name, bs_category=category)
            unit.save()