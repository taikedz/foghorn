#!/usr/bin/env python3

""" Blunt, not subtle.

Broadcast UDP on a common port, advertising name

Listen for others pinging
"""

import argparse
import datetime
import json
import os
import socket
import sqlite3
import threading
import time

MINUTES = 60

PORT = 62001


class Registry:
    def __init__(self, dbfile="peers.sqlite"):
        self._dbfile = dbfile
        self._shared_lock = threading.RLock()

        exists = os.path.exists(self._dbfile)
        self._conn = sqlite3.connect(self._dbfile)

        if not exists:
            self.execute("""
                CREATE TABLE Peers (
                        id int PRIMARY KEY,
                        hostname string,
                        ip string,
                        seen datetime
                        );
                        """)


    def execute(self, command, holders=()):
        assert self._conn is not None, "DB connection not active!"
        with self._shared_lock:
            cursor = self._conn.cursor()
            cursor.execute(command, holders)
            self._conn.commit()


    def register(self, name, ip):
        timestamp = datetime.datetime.now().isoformat()
        self.execute(
            "INSERT INTO Peers (hostname, ip, seen) VALUES (?,?,?)",
            (name, ip, timestamp)
            )
        
    def sweep(self, olderthan):
        """ Select all entries from DB

        Find all that are older than specified date, remove them
        """
        # one-time action

    def ip_of(self, hostname:list[str]|str):
        """ Find all seen IPs for given hostname(s)
        """


    def name_of(self, ip:str):
        """ Find all seen names for given IP
        """


class Sweeper(threading.Thread):
    def __init__(self, registry, sweep_interval):
        threading.Thread.__init__(self, daemon=True)
        self.registry:'Registry' = registry
        self._interval = sweep_interval

    def run(self):
        while True:
            try:
                self.registry.sweep(60 * MINUTES)
                time.sleep(self._interval)
            except KeyboardInterrupt:
                raise
            except Exception as e:
                print(f"Error in sweeper: {e}")


def query(registry:Registry, name, ip):
    print("To be implemented")


def send(send_ip, interval, broadcast, message):
    send_addr = (send_ip, PORT)
    message = {"message": message, "host": socket.gethostname()}

    sock = socket.socket(socket.AF_INET, socket.SOCK_DGRAM)
    if broadcast:
        print("(Broadcast mode - will not work on corporate LAN)")
        sock.setsockopt(socket.SOL_SOCKET, socket.SO_BROADCAST, 1)

    print(f"Pinging to {send_addr}")

    while True:
        sock.sendto(json.dumps(message).encode('utf-8'), send_addr)
        time.sleep(interval)


def listen(registry:Registry, listen_ip, broadcast):
    if listen_ip == "all":
        listen_ip = ""
    bind_addr = (listen_ip, PORT)
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
        # print(f"{address}    {message['host']}")  #  replace with writing to a log


def parse_args():
    parser = argparse.ArgumentParser()

    parser.add_argument("--log", default=None)
    parser.add_argument("--database", "-D", default="peers.sqlite")

    subs = parser.add_subparsers(dest="action", required=True)

    listen_p = subs.add_parser("listen")
    listen_p.add_argument("--bind", default="all")
    listen_p.add_argument("--broadcast", "-B", action="store_true")
    listen_p.add_argument("--sweep-interval", "-N", default=30 * MINUTES)

    send_p = subs.add_parser("send")
    send_p.add_argument("ip")
    send_p.add_argument("--message", "-M", default="CLACK")
    send_p.add_argument("--broadcast", "-B", action="store_true")
    send_p.add_argument("--interval", "-n", default=10 * MINUTES, type=int)

    query_p = subs.add_parser("query")
    query_p.add_argument("--host", "-H")
    query_p.add_argument("--ip", "-P")

    return parser.parse_args()



def main():
    args = parse_args()

    reg = Registry(args.database)

    # Keep alive always
    while True:
        try:
            if args.action == "listen":
                sw = Sweeper(reg, args.sweep_interval)
                sw.start()

                listen(reg, args.bind, args.broadcast)

            elif args.action == "send":
                send(args.ip, args.interval, args.broadcast, args.message)

            elif args.action == "query":
                query(reg, args.host, args.ip)

            else:
                print(f"Unknown action {repr(args.action)} . Run with '--help'")
                exit(1)

        except KeyboardInterrupt: # sigint
            print("\nKTHXBAI")
            return
        except AssertionError as e:
            print(e)
            exit(1)
        except Exception as e:
            print(f"ERROR : {e}")
            print("Starting again....\n=========")


if __name__ == "__main__":
    main()
