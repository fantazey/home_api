import socket
import os
import bluetooth
import time

device_addr = "B7:7B:1A:07:21:AF"
socket_path = "/tmp/homeapi/hangar.sock"
socket_pid = "/tmp/homeapi/server.pid"


def send_command(command):
    sock = bluetooth.BluetoothSocket(bluetooth.RFCOMM)
    port = 1
    print("Connecting to hangar")
    sock.connect((device_addr, port))
    time.sleep(2)
    print("Send command:", command)
    try:
        sock.send('@' + command + '#')
    except Exception:
        time.sleep(2)
        sock.send('@' + command + '#')
    finally:
        time.sleep(1)
        print("Close hangar connection")
        sock.close()


def restart_check():
    if not os.path.exists(socket_pid):
        return False

    with open(socket_pid, 'r') as reader:
        pid = reader.readline()
        if pid is None or len(pid) == 0:
            return False
        exitcode = os.system("ps -o cmd= {}".format(pid))
        if exitcode == 0:
            return True
    return False


def main():
    if restart_check():
        print("Restart check: Server already running. Exit")
        return
    pid = os.getpid()
    with open(socket_pid, 'w') as writer:
        print("Save pid {} to file".format(pid))
        writer.write(str(pid))
    if os.path.exists(socket_path):
        print("Remove old socket file")
        os.remove(socket_path)
    server = socket.socket(socket.AF_UNIX, socket.SOCK_STREAM)
    server.bind(socket_path)
    print("Start server")
    while True:
        server.listen(1)
        conn, addr = server.accept()
        print("Connection accepted")
        bytes_data = conn.recv(1024)
        print("Data received:", bytes_data)
        if not bytes_data:
            continue
        data = bytes_data.decode()
        print("Decoded data:", data)
        send_command(data)
        print("Close client connection")
        conn.close()


if __name__ == "__main__":
    main()
