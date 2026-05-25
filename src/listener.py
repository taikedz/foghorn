import json
import socket
import threading

from foglog import GetLog
import registry

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

            self.registry.register(message['host'], address)
            if message.get("altname"):
                # Register a separate entry explicitly marked as an "alt" name (to avoid silly clashes)
                # If a client says its altname is "testserver", it gets registered as "alt.testserver"
                self.registry.register(f"alt.{message['altname']}", address)

            log.info(f"{address.ljust(15)}    {message['host']} alt={message['altname']}")