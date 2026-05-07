
import datetime
import hashlib
from http.server import BaseHTTPRequestHandler, HTTPServer
from urllib.parse import urlparse, parse_qs
import threading

from const import CONFIG
from foglog import GetLog
import registry


_LOG = GetLog("etc-serv")

def gen_handler_for(ipreg:registry.Registry, access_token:str):
    class RequestHandlerWithRegistry(BaseHTTPRequestHandler):
        REGISTRY = ipreg
        TOKEN = access_token

        def do_GET(self):
            data = parse_qs(urlparse(self.path).query)
            token_values = data.get("token", [])
            if len(token_values) > 1:
                self._write_response(400, "One token at a time.\n")
                return
            elif not token_values or token_values[0] != self.TOKEN:
                self._write_response(403, "No.\n")
                print(f"Got {repr(token_values[0])} instead of {repr(self.TOKEN)}")
                return

            hosts_data = "\r\n".join(
                [f"{ip.ljust(15)}    {' '.join(hostlist)}" for ip, hostlist in self.REGISTRY.get_hosts().items()]
            )
            hosts_data = f"# {datetime.datetime.now().isoformat()}\n\n{hosts_data}\n"

            _LOG.info(f"Request from {self.client_address[0]} : {self.path}")

            self._write_response(200, hosts_data)


        def _write_response(self, code:int, data):
            self.protocol_version = "HTTP/1.1"
            self.send_response(code)
            self.send_header("Content-Length", f"{len(data)}")
            self.end_headers()

            self.wfile.write(bytes(data, "utf8"))

    return RequestHandlerWithRegistry

class EtcHostsServer(threading.Thread):

    def __init__(self, ipreg:registry.Registry, addr, port):
        threading.Thread.__init__(self, daemon=True)
        server = (addr, port)
        # TODO - generate a random hash, print to stderr on-launch
        #        require it as an access token to pass in query string

        access_token = hashlib.sha1(datetime.datetime.now().isoformat().encode("utf-8")).hexdigest()[:10]
        with open(CONFIG.get("TOKEN_FILE") or "./access-token.txt", "w") as fh:
            fh.write(f"{access_token}\n")

        print(f"Etc listening on {server}")
        print(f"Access token = {access_token}")
        self.httpd = HTTPServer(server, gen_handler_for(ipreg, access_token))

    def run(self):
        try:
            # Fixme - writes its own log to stdout/stderr - need to capture
            self.httpd.serve_forever()
        except Exception as e:
            message = f"-- EtcHostsServer {type(e)} : {e}"
            _LOG.error(message)
            print(message)
            raise
