import ipaddress
import time
import json
import socket

from const import CONFIG

def send(send_ip, send_port, interval, broadcast, altname):
    send_addr = (send_ip, send_port)
    message_obj = {"altname": altname, "host": socket.gethostname()}
    message_json = json.dumps(message_obj).encode('utf-8')

    sock = socket.socket(socket.AF_INET, socket.SOCK_DGRAM)
    if broadcast:
        print("(Broadcast mode - may not work on corporate LANs)")
        sock.setsockopt(socket.SOL_SOCKET, socket.SO_BROADCAST, 1)

    print(f"Pinging to {send_addr} every {interval} seconds")

    while True:
        if broadcast:
            # Use _actual_ broadcast
            # This may not be available on corporate networks though
            sock.sendto(message_json, send_addr)
        else:
            _scatter(sock, send_addr, message_json)
        time.sleep(interval)


def _scatter(sock:socket.socket, send_addr:tuple[str,int],message:bytes):
    base_ip, port = send_addr
    for ip in ipaddress.ip_network(base_ip):
        target = (str(ip), port)
        # print(f"Send to {target}")
        try:
            sock.sendto(message, target)
        except PermissionError as e:
            print(f"Warning: Could not send to {target}")


def send_once(ip, port, **extras):
    sock = socket.socket(socket.AF_INET, socket.SOCK_DGRAM)
    message_obj = {"altname": CONFIG.get("ALTNAME"), "host": socket.gethostname()} | extras
    message_json = json.dumps(message_obj).encode('utf-8')
    _scatter(sock, (ip, port), message_json)


def discover(server_ips, port):
    message_obj = {"echo": "true", "host": socket.gethostname()}
    message_json = json.dumps(message_obj).encode('utf-8')

    sock = socket.socket(socket.AF_INET, socket.SOCK_DGRAM)

    for ip in server_ips:
        _scatter(sock, (ip, port), message_json)