#!/usr/bin/env python3

""" Blunt, not subtle.

Broadcast UDP on a common port, advertising name

Listen for others pinging
"""

import argparse
import os
import sqlite3
import time

from const import MINUTES, CONFIG
from foglog import GetLog, InitLogFile
import hostapply
import listener
import registry
import sender
from util import asBool


def parse_args():
    parser = argparse.ArgumentParser()

    parser.add_argument("--log", default=CONFIG.get("LOG"), help="Log file path")
    parser.add_argument("--database", "-D", default=CONFIG.get("DATABASE"), help="Database file for saving/reading entries")

    subs = parser.add_subparsers(dest="action", required=True)

    dump_p = subs.add_parser("dump-config")

    applyhosts_p = subs.add_parser("apply-etc-hosts")

    discover_p = subs.add_parser("discover") # action to send the echo request
    discover_p.add_argument("ips", nargs="+", default=CONFIG.get("SERVER_IP"))
    discover_p.add_argument("--port", "-p", default=CONFIG.getInt("PORT"), type=int, help="Port foe listener to listen on")

    run_p = subs.add_parser("run")
    run_p.add_argument("ip", nargs="?", default=CONFIG.get("SERVER_IP"))

    run_p.add_argument("--bind", default=CONFIG.get("BIND", "0.0.0.0"), help="Address for listener to bind to")
    run_p.add_argument("--port", "-p", default=CONFIG.getInt("PORT"), type=int, help="Port foe listener to listen on")
    run_p.add_argument("--sweep", "-W", choices=["true", "false"], default=CONFIG.get("SWEEP"), help="Whether to remove old entries")
    run_p.add_argument("--sweep-interval", "-N", type=int, default=30 * MINUTES, help="How frequently to sweep the database entries (seconds)")
    run_p.add_argument("--age-limit", "-L", type=int, default=30 * MINUTES, help="Age of entry after which to remove (seconds)")

    run_p.add_argument("--altname", "-A", default=CONFIG.get("ALTNAME"), help="Register an additional alternative hostname")
    run_p.add_argument("--broadcast", "-B", action="store_true", help="Send using broadcast mode (requires supplied IP to be a network CIDR spec)")
    run_p.add_argument("--interval", "-n", default=10 * MINUTES, type=int, help="Interval in seconds, how frequently to ping server")

    query_p = subs.add_parser("query", help="Query local database file")
    query_p.add_argument("--host", "-H", default=None, help="Hostname to get the IP of")
    query_p.add_argument("--ip", "-P", default=None, help="IP to get the hostname of")
    query_p.add_argument("--dump", action="store_true", help="Dump all entries")
    query_p.add_argument("--latest", action="store_true", help="Dump latest entries")
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
        "latest": args.latest,
    }
    assert len([x for x in relevant.values() if x not in [None,False]]) == 1, f"Specify one of {', '.join(relevant.keys())}"

    print(f"Reading from {reg.filepath()}")

    if relevant["ip"] is not None:
        reg.name_of(relevant["ip"])
    if relevant["host"] is not None:
        reg.ip_of(relevant["host"])
    if relevant["dump"]:
        reg.dump()
    if relevant["latest"]:
        reg.latest_pairs()
    if relevant["hosts"]:
        reg.print_hosts()


def main():
    args = parse_args()

    # Initialize now, before other modules get involved
    if args.log:
        InitLogFile(args.log)
    log = GetLog("foghorn")

    while True:
        try:
            if args.action == "dump-config":
                print(CONFIG.asDict())
                return
            
            elif args.action == "apply-etc-hosts":
                reg = registry.Registry(args.database)
                hosts = reg.get_hosts()
                hostapply.apply_hosts([f"{ip}  {' '.join(hostlist)}" for ip, hostlist in hosts.items()])
                return

            elif args.action == "query":
                reg = registry.Registry(args.database, readonly=True)
                do_query(reg, args)
                return
            
            elif args.action == "discover":
                reg = registry.Registry(args.database)
                sender.discover(args.ips, args.port, reg)
                return


            elif args.action == "run":

                reg = registry.Registry(args.database)

                if asBool(args.sweep):
                    sw = registry.Sweeper(args.database, args.sweep_interval, args.age_limit)
                    sw.start()

                ears = listener.Listener(reg, args.bind, args.port, args.broadcast)
                ears.start()

                # Arbitrarily wait til listener has started
                time.sleep(0.01)

                # This will cause all hosts to ping-back, seeding our listener
                #  with available IPs. Causes quite a bit of extra chatter
                sender.discover([args.ip], args.port, reg)

                # This is to just do the regular send at intervals, with no ping-back request
                sender.send(args.ip, args.port, args.interval, args.broadcast, args.altname)

            else:
                print(f"Unknown action {repr(args.action)} . Run with '--help'")
                exit(1)

        except KeyboardInterrupt: # sigint
            print("\nKTHXBAI")
            return
        except (AssertionError, OSError) as e:
            print(f"OS error: {e}")
            if "Network is unreachable" in str(e):
                # We certainly want to keep going in this case
                time.sleep(30)
                continue
            # Other OSError instances might be less of a bother
            print("FATAL.")
            exit(1)
        except (ValueError, AssertionError, KeyError, TypeError, AttributeError):
            raise
        except sqlite3.OperationalError as e:
            print(f"FATAL : {e}")
            exit(99)
        except Exception as e:
            print(f"ERROR : {type(e)}:{e}")
            print("Starting again....\n=========")
            time.sleep(2) # If there's an irremediable error, loop slowly ...


if __name__ == "__main__":
    main()
