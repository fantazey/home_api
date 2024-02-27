import socket

socket_path = "/tmp/hangar.sock"


def send_command(command):
    client = socket.socket(socket.AF_UNIX, socket.SOCK_STREAM)
    client.connect(socket_path)
    print("Send command", str.encode(command))
    client.send(str.encode(command))
    client.close()


def brightness_command(value: str):
    command = "B" + value +"L3"
    send_command(command)


def light_level6():
    command = "L6"
    send_command(command)


def light_level5():
    command = "L4"
    send_command(command)


def light_level4():
    command = "L4"
    send_command(command)


def light_level3():
    command = "L3"
    send_command(command)


def light_level0():
    command = "L0"
    send_command(command)