#!/usr/bin/env python3

""" Blunt, not subtle.

Broadcast UDP on a common port, advertising name

Listen for others pinging
"""

import argparse
import time

from const import MINUTES, CONFIG
import config
from hostserver import EtcHostsServer
import listener
import registry
import sender
from util import asBool





def parse_args():
    parser = argparse.ArgumentParser()

    parser.add_argument("--log", default=None) # NOT IMPLEMENTED
    parser.add_argument("--database", "-D", default=CONFIG.get("DATABASE"))

    subs = parser.add_subparsers(dest="action", required=True)

    listen_p = subs.add_parser("dump-config")

    listen_p = subs.add_parser("listen")
    listen_p.add_argument("--bind", default=CONFIG.get("BIND"))
    listen_p.add_argument("--broadcast", "-B", action="store_true")
    listen_p.add_argument("--sweep", "-W", choices=["true", "false"], default=CONFIG.get("SWEEP"))
    listen_p.add_argument("--etc-hosts-server", "-E", choices=["true", "false"], default=CONFIG.get("ETC_HOSTS_SERVER"))
    listen_p.add_argument("--sweep-interval", "-N", type=int, default=30 * MINUTES, help="How frequently to sweep the database entries (seconds)")
    listen_p.add_argument("--age-limit", "-L", type=int, default=30 * MINUTES, help="Age of entry after which to remove (seconds)")

    send_p = subs.add_parser("send")
    send_p.add_argument("ip", nargs="?", default=CONFIG.get("SERVER_IP"))
    send_p.add_argument("--message", "-M", default="CLACK")
    send_p.add_argument("--broadcast", "-B", action="store_true")
    send_p.add_argument("--interval", "-n", default=10 * MINUTES, type=int)

    query_p = subs.add_parser("query")
    query_p.add_argument("--host", "-H", default=None, help="Hostname to get the IP of")
    query_p.add_argument("--ip", "-P", default=None, help="IP to get the hostname of")
    query_p.add_argument("--dump", action="store_true", help="Dump entries")
    query_p.add_argument("--hosts", action="store_true", help="Print entries in /etc/hosts compatible format")

    return parser.parse_args()


def do_query(reg:registry.Registry, args:argparse.Namespace):
    # FIXME - this will access the sqlite db file from an _entirely unrelated process_
    #         which means that no threading lock will actually work
    #         Either implement a filesystem based lock, or use an API on localhost
    relevant = {
        "ip": args.ip,
        "host": args.host,
        "dump": args.dump,
        "hosts": args.hosts,
    }
    assert len([x for x in relevant.values() if x not in [None,False]]) == 1, f"Specify one of {', '.join(relevant.keys())}"

    if relevant["ip"] is not None:
        reg.name_of(relevant["ip"])
    if relevant["host"] is not None:
        reg.ip_of(relevant["host"])
    if relevant["dump"]:
        reg.dump()
    if relevant["hosts"]:
        reg.print_hosts()


def main():
    args = parse_args()

    reg = registry.Registry(args.database)

    try:
        if args.action == "dump-config":
            print(CONFIG.asDict())

        elif args.action == "listen":

            if asBool(args.sweep):
                sw = registry.Sweeper(args.database, args.sweep_interval, args.age_limit)
                sw.start()

            if asBool(args.etc_hosts_server):
                hs = EtcHostsServer(reg)
                hs.start()

            listener.listen(reg, args.bind, args.broadcast)

        elif args.action == "send":
            sender.send(args.ip, args.interval, args.broadcast, args.message)

        elif args.action == "query":
            do_query(reg, args)
            return

        else:
            print(f"Unknown action {repr(args.action)} . Run with '--help'")
            exit(1)

    except KeyboardInterrupt: # sigint
        print("\nKTHXBAI")
        return
    except AssertionError as e:
        print(e)
        exit(1)
    except (ValueError, AssertionError, KeyError, AttributeError):
        raise
    except Exception as e:
        print(f"ERROR : {e}")
        print("Starting again....\n=========")
        time.sleep(0.5)


if __name__ == "__main__":
    main()
