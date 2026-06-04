import json
import socket
import threading

from foglog import GetLog
import registry
import sender

def dolog(fn, message):
    fn(message)
    print(message)

class Listener(threading.Thread):

    def __init__(self, registry:registry.Registry, listen_ip, listen_port, broadcast):
        threading.Thread.__init__(self, daemon=True)

        self.registry = registry
        self.listen_ip = listen_ip
        self.listen_port = listen_port
        self.broadcast = broadcast

    def run(self):

        log = GetLog("listener")

        bind_addr = (self.listen_ip, self.listen_port )
        dolog(log.info, f"Listening on {bind_addr}")

        ssock = socket.socket(socket.AF_INET, socket.SOCK_DGRAM, socket.IPPROTO_UDP)
        ssock.bind(bind_addr)

        if self.broadcast:
            log.debug("Activate broadcast")
            ssock.setsockopt(socket.SOL_SOCKET, socket.SO_REUSEPORT, 1)
            ssock.setsockopt(socket.SOL_SOCKET, socket.SO_BROADCAST, 1)

        while True:
            data, endpoint = ssock.recvfrom(1024)
            address, _port = endpoint
            message = json.loads(data.decode('utf-8'))

            # print(f"Got from {address} : {message}")

            self.registry.register(message['host'], address)
            if message.get("altname"):
                # Register a separate entry explicitly marked as an "alt" name (to avoid silly clashes)
                # If a client says its altname is "testserver", it gets registered as "testserver.fog"
                self.registry.register(f"{message['altname']}.fog", address)

            if message.get("echo", "false").lower() == "true":
                log.info(f"Replying to {address}")
                # print(f"Send-back : {address}")
                sender.send_once(address, self.listen_port, reason="echo")

            log.info(f"{address.ljust(15)}    {message.get('host')} alt={message.get('altname')}")