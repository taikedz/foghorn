""" Await HOST --ssh SHELL_COMMAND

Continually check until named host appears; when we find the hostname in the registry,
optionally run a command against the host immediately, or print the hostname and the time iot was detected.
"""

# TODO - implement with paramiko to pass in password and ignore host check, for blanket SSH command running

import datetime
import os
import shlex
import sys
import threading
import time

import registry


def await_hosts(db_path:str, hosts:list[str], shell_command=None, timeout:int=0, user=None):
    reg = registry.Registry(db_path, readonly=True)
    all_waiters = []

    for host in hosts:
        waiter = AwaitHost(reg, host, shell_command, timeout=timeout, user=user)
        waiter.start()
        all_waiters.append(waiter)

    for w in all_waiters:
        w.join()


class AwaitHost(threading.Thread):
    def __init__(self, reg:registry.Registry, host:str, shell_command:str, timeout:int=0, user=None):
        threading.Thread.__init__(self, daemon=True)

        self._reg = reg
        self._host = host
        self._timeout = timeout
        self._command = shell_command
        self._user = user


    def run(self):
        start = datetime.datetime.now()
        while self._timeout <= 0 or (self._timeout > 0 and (datetime.datetime.now() - start).total_seconds() < self._timeout):
            try:
                ip = self._reg.latest_ip_of(self._host)
                if ip is None:
                    ip = self._reg.latest_ip_of(f"{self._host}.fog")
                if ip is None:
                    continue

                if self._command:
                    user = f"{self._user}@" if self._user else ""
                    plain_command = shlex.join(["ssh", "-t", f"{user}{ip}", self._command])
                    print(f"Running: {repr(plain_command)}", file=sys.stderr)
                    os.system(plain_command)
                else:
                    print(f"{ip.ljust(15)}{self._host} # {datetime.datetime.now()}")
                return
            finally:
                time.sleep(1)

        print(f"# TIMEOUT : {self._host}")