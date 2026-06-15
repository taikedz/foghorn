import ipaddress
import select
import time
import json
import socket

from const import CONFIG
import registry
import foglog

ALTNAME = None

def set_altname(altname):
    global ALTNAME
    ALTNAME = altname


def send(send_ip_list, send_port, interval):
    message_obj = {"altname": ALTNAME, "host": socket.gethostname()}
    message_json = json.dumps(message_obj).encode('utf-8')

    log_ = foglog.GetLog("send")
    log_.info(f"INTEVAL = {interval}")
    log_.info(f"DEST = {send_ip_list}")

    sock = socket.socket(socket.AF_INET, socket.SOCK_DGRAM)

    while True:
        for send_ip in send_ip_list:
            send_addr = (send_ip, send_port)
            _scatter(sock, send_addr, message_json)
        time.sleep(interval)


def _scatter(sock:socket.socket, send_addr:tuple[str,int],message:bytes):
    log_ = foglog.GetLog("send")

    base_ip, port = send_addr
    for ip in ipaddress.ip_network(base_ip):
        target = (str(ip), port)
        try:
            sock.sendto(message, target)
        except PermissionError as e:
            # Very likely a broadcast destination
            log_.info(f"Warning: Could not send to {target}")


def send_once(ip, port, **extras):
    sock = socket.socket(socket.AF_INET, socket.SOCK_DGRAM)
    message_obj = {"altname": ALTNAME, "host": socket.gethostname()} | extras
    message_json = json.dumps(message_obj).encode('utf-8')
    _scatter(sock, (ip, port), message_json)


def discover(server_ips, port, reg:registry.Registry, to_server=True):
    message_obj = {
        "echo": "server" if to_server else "origin",
        "host": socket.gethostname(),
        "altname": ALTNAME,
        }
    message_json = json.dumps(message_obj).encode('utf-8')
    sock = socket.socket(socket.AF_INET, socket.SOCK_DGRAM)

    if to_server:
        for base_ip in server_ips:
            _scatter(sock, (base_ip, port), message_json)
    else:
        sock.setblocking(False)
        timeout_seconds = 0.05

        # Reference for this loop: _scatter() function, above
        for base_ip in server_ips:
            for ip in ipaddress.ip_network(base_ip):
                target = (str(ip), port)
                try:
                    sock.sendto(message_json, target)
                    ready = select.select([sock], [], [], timeout_seconds)
                    if ready[0]:
                        response, endpoint = sock.recvfrom(1024)
                        address, _port = endpoint
                        message = json.loads(response.decode("utf-8"))
                        if reg is None:
                            print(message) # .... put this elsewhere ?
                        else:
                            reg.register(message.get("host"), address, message.get("altname"))


                except PermissionError:
                    print(f"Warning: Could not send to {target}")
