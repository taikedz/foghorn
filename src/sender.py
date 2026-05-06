import time
import json
import socket


def send(send_ip, send_port, interval, broadcast, altname):
    send_addr = (send_ip, send_port)
    message = {"altname": altname, "host": socket.gethostname()}

    sock = socket.socket(socket.AF_INET, socket.SOCK_DGRAM)
    if broadcast:
        print("(Broadcast mode - may not work on corporate LANs)")
        sock.setsockopt(socket.SOL_SOCKET, socket.SO_BROADCAST, 1)

    print(f"Pinging to {send_addr} every {interval} seconds")

    while True:
        sock.sendto(json.dumps(message).encode('utf-8'), send_addr)
        time.sleep(interval)