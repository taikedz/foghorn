import time
import json
import socket

from const import CONFIG


def send(send_ip, interval, broadcast, message):
    if send_ip is None:
        send_ip = CONFIG.get("SERVER_IP")
    assert send_ip, f"Server IP specified in neither arguments nor config."

    send_addr = (send_ip, int(CONFIG.get("PORT")))
    message = {"message": message, "host": socket.gethostname()}

    sock = socket.socket(socket.AF_INET, socket.SOCK_DGRAM)
    if broadcast:
        print("(Broadcast mode - will not work on corporate LAN)")
        sock.setsockopt(socket.SOL_SOCKET, socket.SO_BROADCAST, 1)

    print(f"Pinging to {send_addr}")

    while True:
        sock.sendto(json.dumps(message).encode('utf-8'), send_addr)
        time.sleep(interval)