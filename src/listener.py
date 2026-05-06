import json
import socket

import registry
from const import CONFIG

def listen(registry:registry.Registry, listen_ip, listen_port, broadcast):

    bind_addr = (listen_ip, listen_port )
    print(f"Listening on {bind_addr}")

    ssock = socket.socket(socket.AF_INET, socket.SOCK_DGRAM, socket.IPPROTO_UDP)
    ssock.bind(bind_addr)

    if broadcast:
        ssock.setsockopt(socket.SOL_SOCKET, socket.SO_REUSEPORT, 1)
        ssock.setsockopt(socket.SOL_SOCKET, socket.SO_BROADCAST, 1)

    while True:
        data, endpoint = ssock.recvfrom(1024)
        address, _port = endpoint
        message = json.loads(data.decode('utf-8'))
        registry.register(message['host'], address)
        #print(f"{address}    {message['host']}")  #  replace with writing to a log