
import datetime
from http.server import BaseHTTPRequestHandler, HTTPServer
import threading

import registry
from const import CONFIG


def gen_handler_for(ipreg:registry.Registry):
    class RequestHandlerWithRegistry(BaseHTTPRequestHandler):
        REGISTRY = ipreg

        def do_GET(self):
            hosts_data = "\r\n".join(
                [f"{ip.ljust(15)}    {' '.join(hostlist)}" for ip, hostlist in self.REGISTRY.get_hosts().items()]
            )
            hosts_data = f"# {datetime.datetime.now().isoformat()}\n\n{hosts_data}\n"

            self.protocol_version = "HTTP/1.1"
            self.send_response(200)
            self.send_header("Content-Length", f"{len(hosts_data)}")
            self.end_headers()

            self.wfile.write(bytes(hosts_data, "utf8"))

    return RequestHandlerWithRegistry

class EtcHostsServer(threading.Thread):

    def __init__(self, ipreg:registry.Registry):
        threading.Thread.__init__(self, daemon=True)
        server = (CONFIG.get("BIND") or "", CONFIG.int("HTTP_PORT"))
        print(f"Etc listening on {server}")
        self.httpd = HTTPServer(server, gen_handler_for(ipreg))

    def run(self):
        try:
            self.httpd.serve_forever()
        except Exception as e:
            print(f"-- EtcHostsServer err : {e}")
            raise
