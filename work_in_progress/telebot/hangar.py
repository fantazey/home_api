import socket
from django.utils import timezone

socket_path = "/tmp/homeapi/hangar.sock"

D_SHUFFLE = 0  # переключение всех режимов по таймауту
D_YEAR = 1  # показать год
D_MIN_SEC = 2  # показать минуты и секунды
D_DHT_TEMP = 3  # показать температуру с DHT11
D_DATE_MON = 4  # показать день и месяц
D_HOUR_MIN = 5  # показать часы и минуты
D_BMP_TEMP = 6  # показать температуру с BMP280
D_BMP_PRESS = 7  # показать давление с BMP280
D_DHT_HUM = 8  # показать влажность с DHT11
D_LUX = 9  # показать интенсивность света
D_PAINTED = 10  # показать количество покрашеных миниатюр
D_UNPAINTED = 11  # показать количество непокрашеных миниатюр

L_OFF = 0  # свет выкл
L_DYNAMIC = 1  # динамический свет зависящий от датчика интенсивности
L_FADE = 2  # мигающий свет
L_FIXED = 3  # фиксированная яркость установленная руками
L_LOW = 4  # тусклый свет
L_MID = 5  # средний свет
L_HIGH = 6  # полная яркость

COMMANDS = {
    'hour': 'H',
    'minute': 'M',
    'second': 'S',
    'year': 'y',
    'month': 'm',
    'day': 'd',
    'display_mode': 'D',
    'light_mode': 'L',
    'lux_sensor_multiplier': 'l',
    'brightness': 'B',
    'painted': 'P',
    'unpainted': 'U'
}


def sync_time():
    time_now = timezone.now() + timezone.timedelta(seconds=20)
    command = f"{COMMANDS['hour']}{time_now.hour}" \
              f"{COMMANDS['minute']}{time_now.minute}" \
              f"{COMMANDS['second']}{time_now.second}"
    _send_command(command)


def set_light_full():
    _set_light_mode(L_HIGH)


def set_light_mid():
    _set_light_mode(L_MID)


def set_light_low():
    _set_light_mode(L_LOW)


def set_light_off():
    _set_light_mode(L_OFF)


def set_light_fade():
    _set_light_mode(L_FADE)


def set_light_value(value: int):
    if value == 0:
        set_light_off()
        return
    _set_light_mode(L_FIXED)
    _set_brightness(value)


def _set_light_mode(mode: int):
    _send_command(COMMANDS['light_mode'] + str(mode))


def _set_brightness(level: int):
    level = level % 256
    _send_command(COMMANDS['brightness'] + str(level))


def set_painted_count(count: int):
    _send_command(COMMANDS['painted'] + str(count))


def set_unpainted_count(count: int):
    _send_command(COMMANDS['unpainted'] + str(count))


def display_show_all():
    _set_display_mode(D_SHUFFLE)


def display_show_date():
    _set_display_mode(D_DATE_MON)


def display_show_painted():
    _set_display_mode(D_PAINTED)


def display_show_unpainted():
    _set_display_mode(D_UNPAINTED)


def _set_display_mode(mode: int):
    _send_command(COMMANDS['display_mode'] + str(mode))


def _send_command(command):
    client = socket.socket(socket.AF_UNIX, socket.SOCK_STREAM)
    client.connect(socket_path)
    data = str.encode(command)
    print("Send command", data)
    client.send(data)
    client.close()
