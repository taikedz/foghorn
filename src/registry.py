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
                        id INTEGER PRIMARY KEY,
                        hostname STRING,
                        ip STRING,
                        seen DATETIME
                        );
                        """)


    def execute(self, command, holders=()):
        assert self._conn is not None, "DB connection not active!"
        with self._shared_lock:
            cursor = self._conn.cursor()
            cursor.execute(command, holders)
            self._conn.commit()


    def select(self, command, holders=()) -> list[list]:
        assert self._conn is not None, "DB connection not active!"
        with self._shared_lock:
            cursor = self._conn.cursor()
            cursor.execute(command, holders)
            rows = cursor.fetchall()
            self._conn.commit()
        return rows


    def register(self, name, ip):
        timestamp = datetime.datetime.now().isoformat()
        self.execute(
            "INSERT INTO Peers (hostname, ip, seen) VALUES (?,?,?)",
            (name, ip, timestamp)
            )
        
    def sweep(self, olderthan:datetime.datetime):
        """ Select all entries from DB

        Find all that are older than specified date, remove them
        """
        peers = self.select("SELECT id,seen FROM Peers")
        rmpeers = {id:dt for id,dt in peers if datetime.datetime.fromisoformat(dt) < olderthan}
        #print(f"Should remove {rmpeers}")
        for id in rmpeers.keys():
            self.execute("DELETE FROM Peers WHERE id = ?;", (id, ))

    def ip_of(self, hostname:str):
        """ Find all seen IPs for given hostname(s)
        """
        res = self.select("SELECT ip FROM Peers WHERE hostname = ?;", (hostname,))
        print("\n".join(list(set([v[0] for v in res]))))


    def name_of(self, ip:str):
        """ Find all seen names for given IP
        """
        res = self.select("SELECT hostname FROM Peers WHERE ip = ?;", (ip,))
        print("\n".join(list(set([v[0] for v in res]))))


    def dump(self):
        """ Print all entries
        """
        res = self.select("SELECT seen,ip,hostname FROM Peers;")
        print("\n".join(
            list(set([f"{i} {h}   # {t}" for t,i,h in res]))
            )
        )


    def hosts(self):
        """ Print all entries
        """
        res = self.select("SELECT ip,hostname FROM Peers;")
        ips = {}
        for ip,hostname in res:
            if ip not in ips:
                ips[ip] = []
            if hostname not in ips[ip]:
                ips[ip].append(hostname)

        for ip, hostlist in ips.items():
            print(f"{ip}  {' '.join(hostlist)}")


class Sweeper(threading.Thread):
    def __init__(self, dbfile, sweep_interval, age_limit):
        threading.Thread.__init__(self, daemon=True)
        self._dbfile = dbfile
        self._interval = sweep_interval # seconds
        self._limit = age_limit

    def run(self):
        registry = Registry(self._dbfile)
        while True:
            try:
                oldest = datetime.datetime.now() - datetime.timedelta(seconds=self._limit)
                registry.sweep(oldest)
            except KeyboardInterrupt:
                raise
            except Exception as e:
                print(f"Error in sweeper: {e}")
            time.sleep(self._interval)