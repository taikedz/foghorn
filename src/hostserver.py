
import datetime
from http.server import BaseHTTPRequestHandler, HTTPServer
import threading

from foglog import GetLog
import registry


_LOG = GetLog("etc-serv")

def gen_handler_for(ipreg:registry.Registry):
    class RequestHandlerWithRegistry(BaseHTTPRequestHandler):
        REGISTRY = ipreg

        def do_GET(self):
            hosts_data = "\r\n".join(
                [f"{ip.ljust(15)}    {' '.join(hostlist)}" for ip, hostlist in self.REGISTRY.get_hosts().items()]
            )
            hosts_data = f"# {datetime.datetime.now().isoformat()}\n\n{hosts_data}\n"

            _LOG.info(f"Request from {self.client_address[0]} : {self.path}")

            self.protocol_version = "HTTP/1.1"
            self.send_response(200)
            self.send_header("Content-Length", f"{len(hosts_data)}")
            self.end_headers()

            self.wfile.write(bytes(hosts_data, "utf8"))

    return RequestHandlerWithRegistry

class EtcHostsServer(threading.Thread):

    def __init__(self, ipreg:registry.Registry, addr, port):
        threading.Thread.__init__(self, daemon=True)
        server = (addr, port)
        # TODO - generate a random hash, print to stderr on-launch
        #        require it as an access token to pass in query string
        print(f"Etc listening on {server}")
        self.httpd = HTTPServer(server, gen_handler_for(ipreg))

    def run(self):
        try:
            # Fixme - writes its own log to stdout/stderr - need to capture
            self.httpd.serve_forever()
        except Exception as e:
            message = f"-- EtcHostsServer {type(e)} : {e}"
            _LOG.error(message)
            print(message)
            raise
