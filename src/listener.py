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

    def __init__(self, registry:registry.Registry, listen_ip, listen_port):
        threading.Thread.__init__(self, daemon=True)

        self.registry = registry
        self.listen_ip = listen_ip
        self.listen_port = listen_port

    def run(self):

        log = GetLog("listener")

        bind_addr = (self.listen_ip, self.listen_port )
        dolog(log.info, f"Listening on {bind_addr}")

        ssock = socket.socket(socket.AF_INET, socket.SOCK_DGRAM, socket.IPPROTO_UDP)
        ssock.bind(bind_addr)

        while True:
            data, endpoint = ssock.recvfrom(1024)
            address, response_port = endpoint
            message = json.loads(data.decode('utf-8'))

            # print(f"Got from {address} : {message}")

            self.registry.register(message['host'], address, message.get("altname"))

            log.info(f"{address.ljust(15)}    {message.get('host')} alt={message.get('altname')}")

            echo_mode = message.get("echo", "").lower()
            if echo_mode in ["server", "origin"]:
                log.info(f"Replying to {address} {echo_mode}")

                if echo_mode == "origin":
                    sender.send_once(address, response_port)
                else:
                    sender.send_once(address, self.listen_port)
