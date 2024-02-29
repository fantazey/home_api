import socket
import os
import bluetooth

device_addr = "B7:7B:1A:07:21:AF"
socket_path = "/tmp/homeapi/hangar.sock"


def send_command(command):
    sock = bluetooth.BluetoothSocket(bluetooth.RFCOMM)
    port = 1
    print("Connecting to hangar")
    sock.connect((device_addr, port))
    print("Send command:", command)
    sock.send('@' + command + '#')
    print("Close hangar connection")
    sock.close()


def main():
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
