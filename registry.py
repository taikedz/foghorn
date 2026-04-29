import os
import time
import sqlite3
import datetime
import threading

from const import MINUTES

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
            except KeyboardInterrupt:
                raise
            except Exception as e:
                print(f"Error in sweeper: {e}")
            time.sleep(self._interval)