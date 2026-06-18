#!/usr/bin/env python3

""" Blunt, not subtle.

Broadcast UDP on a common port, advertising name

Listen for others pinging
"""

import argparse
import sqlite3
import time

import awaiter
from const import MINUTES, CONFIG
from foglog import GetLog, InitLogFile
import hostapply
import listener
import registry
import sender
import signalhandle
import querying
from util import asBool


def parse_args():
    parser = argparse.ArgumentParser()

    parser.add_argument("--log", default=CONFIG.get("LOG"), help="Log file path")
    parser.add_argument("--database", "-D", default=CONFIG.get("DATABASE"), help="Database file for saving/reading entries")

    subs = parser.add_subparsers(dest="action", required=True)

    dump_p = subs.add_parser("dump-config")

    applyhosts_p = subs.add_parser("apply-etc-hosts")

    discover_p = subs.add_parser("discover") # action to send the echo request
    discover_p.add_argument("ips", nargs="+", help="IPs to ping, which should respond back to us")
    discover_p.add_argument("--altname", "-A", default=CONFIG.get("ALTNAME"), help="Register an additional alternative hostname")
    discover_p.add_argument("--port", "-p", default=CONFIG.getInt("PORT"), type=int, help="Port to send on")
    discover_p.add_argument("--nat-origin", "-O", action="store_true", help="Attempt to have servers respond back to UDP through NAT")

    ping_p = subs.add_parser("ping")
    ping_p.add_argument("ip", help="The IP to send a single discovery ping to")
    ping_p.add_argument("--altname", "-A", default=CONFIG.get("ALTNAME"), help="Register an additional alternative hostname")
    ping_p.add_argument("--port", "-p", default=CONFIG.getInt("PORT"), type=int, help="Port to send on")

    await_p = subs.add_parser("await")
    await_p.add_argument("hosts", nargs="+", help="Host names to await")
    await_p.add_argument("--ssh", help="SSH command to run once host is found")
    await_p.add_argument("--user", help="User for ssh command")
    await_p.add_argument("--timeout", type=int, default=0, help="Seconds to wait before timing out")

    run_p = subs.add_parser("run")
    run_p.add_argument("ips", nargs="*", default=CONFIG.get("SERVER_IP", "127.0.0.1").split(","), help="The IPs/subnets to regularly ping (comma-separated list)")

    run_p.add_argument("--bind", default=CONFIG.get("BIND", "0.0.0.0"), help="Address for listener to bind to")
    run_p.add_argument("--port", "-p", default=CONFIG.getInt("PORT"), type=int, help="Port for listener to listen on")
    run_p.add_argument("--sweep", "-W", choices=["true", "false"], default=CONFIG.get("SWEEP"), help="Whether to remove old entries")
    run_p.add_argument("--sweep-interval", "-N", type=int, default=30 * MINUTES, help="How frequently to sweep the database entries (seconds)")
    run_p.add_argument("--age-limit", "-L", type=int, default=30 * MINUTES, help="Age of entry after which to remove (seconds)")

    run_p.add_argument("--altname", "-A", default=CONFIG.get("ALTNAME"), help="Register an additional alternative hostname")
    run_p.add_argument("--interval", "-n", default=10 * MINUTES, type=int, help="Interval in seconds, how frequently to ping server")

    query_p = subs.add_parser("query", help="Query local database file")
    query_p.add_argument("--host", "-H", default=None, help="Hostname to get the IP of")
    query_p.add_argument("--ip", "-P", default=None, help="IP to get the hostname of")
    query_p.add_argument("--dump", action="store_true", help="Dump all entries")
    query_p.add_argument("--latest", action="store_true", help="Dump latest entries")
    query_p.add_argument("--hosts", action="store_true", help="Print entries in /etc/hosts compatible format")

    return parser.parse_args()



def main():
    args = parse_args()

    # Initialize now, before other modules get involved
    if args.log:
        InitLogFile(args.log)
    log = GetLog("foghorn")

    signalhandle.setup()
    if hasattr(args, "altname"):
        sender.set_altname(args.altname)

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
                querying.do_query(reg, args)
                return
            
            elif args.action == "discover":
                reg = registry.Registry(args.database)
                as_server = not args.nat_origin
                sender.discover(args.ips, args.port, reg, to_server=as_server)
                return

            elif args.action == "ping":
                sender.discover([args.ip], args.port, None, to_server=False)
                return

            elif args.action == "await":
                awaiter.await_hosts(args.database, args.hosts, args.ssh, args.timeout, args.user)
                return

            elif args.action == "run":
                reg = registry.Registry(args.database)

                if asBool(args.sweep):
                    sw = registry.Sweeper(args.database, args.sweep_interval, args.age_limit)
                    sw.start()

                ears = listener.Listener(reg, args.bind, args.port)
                ears.start()

                # Arbitrarily wait til listener has started
                time.sleep(0.01)

                # This will cause all hosts to ping-back, seeding our listener
                #  with available IPs.
                sender.discover(args.ips, args.port, reg)

                # This is to just do the regular send at intervals, with no ping-back request
                sender.send(args.ips, args.port, args.interval)

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
                log.warning(str(e))
                time.sleep(30)
                continue
            # Other OSError instances might be less of a bother
            log.error("FATAL.")
            exit(1)
        except (ValueError, AssertionError, KeyError, TypeError, AttributeError):
            raise
        except sqlite3.OperationalError as e:
            print(f"FATAL : {e}")
            log.error(e)
            exit(99)
        except Exception as e:
            log.error(f"{type(e)}:{e}")
            log.info("-- Restart")
            print("Starting again....\n=========")
            time.sleep(2) # If there's an irremediable error, loop slowly ...


if __name__ == "__main__":
    main()
