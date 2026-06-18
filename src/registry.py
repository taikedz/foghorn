import os
import re
import time
import sqlite3
import datetime
import threading

from foglog import GetLog

NAMEPAT=re.compile(r"^[a-zA-Z][a-zA-Z0-9_-]+$")

class Registry:
    # All instances will share this lock, this is intentional.
    #  It seems sqlite connections do _not_ multithread, so we
    #  need to prevent different registry instances from colliding.
    # NOTE - this is not shared across processes!
    REGISTRY_LOCK = threading.RLock()

    def __init__(self, dbfile:str, readonly=False):
        self.log = GetLog("registry")
        self.log.info(f"Using database file {repr(dbfile)}")
        self._dbfile = dbfile
        self._dbaccess = dbfile
        self._dbaccess_uri = False
        if readonly:
            self._dbaccess = f"file:{dbfile}?mode=ro"
            self._dbaccess_uri = True

        exists = os.path.exists(self._dbfile)

        if not exists and not readonly:
            self.log.info("Creating new tables")
            self.execute("""
                CREATE TABLE Peers (
                        id INTEGER PRIMARY KEY,
                        hostname STRING,
                        ip STRING,
                        seen DATETIME
                        );
                        """)
            

    def filepath(self):
        return self._dbfile
    

    def connect(self):
        return sqlite3.connect(self._dbaccess, uri=self._dbaccess_uri)


    def execute(self, command, holders=()):
        with self.REGISTRY_LOCK, self.connect() as dbconn:
            cursor = dbconn.cursor()
            cursor.execute(command, holders)
            dbconn.commit()


    def select(self, command, holders=()) -> list[list]:
        with self.REGISTRY_LOCK, self.connect() as dbconn:
            cursor = dbconn.cursor()
            cursor.execute(command, holders)
            rows = cursor.fetchall()
            dbconn.commit()
        return rows


    def register(self, name, ip, altname=None):
        timestamp = datetime.datetime.now().isoformat()
        self.execute(
            "INSERT INTO Peers (hostname, ip, seen) VALUES (?,?,?)",
            (name, ip, timestamp)
            )
        if altname:
            # Register a separate entry explicitly marked as an "alt" name (to avoid silly clashes)
            # If a client says its altname is "testserver", it gets registered as "testserver.fog"
            # We split along whitespace to avoid evading our fogging of names
            altnames = altname.split()
            for altname_x in altnames:
                if not re.match(NAMEPAT, altname_x):
                    continue
                self.execute(
                    "INSERT INTO Peers (hostname, ip, seen) VALUES (?,?,?)",
                    (f"{altname_x}.fog", ip, timestamp)
                    )
        
    def sweep(self, olderthan:datetime.datetime):
        """ Select all entries from DB

        Find all that are older than specified date, remove them
        """
        peers = self.select("SELECT id,seen FROM Peers")
        rmpeers = {id:dt for id,dt in peers if datetime.datetime.fromisoformat(dt) < olderthan}
        self.log.debug(f"Removing {len(rmpeers)} stale entries.")
        for id in rmpeers.keys():
            self.execute("DELETE FROM Peers WHERE id = ?;", (id, ))

    def ips_of(self, hostname:str):
        """ Find all seen IPs for given hostname(s)
        """
        res = self.select("SELECT ip FROM Peers WHERE hostname = ?;", (hostname,))
        return list(set([v[0] for v in res]))


    def latest_ip_of(self, hostname:str) -> str|None:
        res = self.select("SELECT seen,ip FROM Peers WHERE hostname = ?;", (hostname,))
        if res:
            res.sort(key=lambda part:datetime.datetime.fromisoformat(part[0]))
            return res[-1][1]
        else:
            return None


    def names_of(self, ip:str):
        """ Find all seen names for given IP
        """
        res = self.select("SELECT hostname FROM Peers WHERE ip = ?;", (ip,))
        return list(set([v[0] for v in res]))


    def entry_lines(self):
        """ Print all entries
        """
        res = self.select("SELECT seen,ip,hostname FROM Peers;")
        res.sort(key=lambda arr:(datetime.datetime.fromisoformat(arr[0]), arr[2].lower()))
        namemax = max([len(h) for t,i,h in res])
        return [f"{i.ljust(15)} {h.ljust(namemax)}   # {t}" for t,i,h in res]


    def latest_pairs(self):
        res = self.select("SELECT seen,ip,hostname FROM Peers;")

        redux = {}
        for d,i,h in res:
            k=(i,h)
            d = datetime.datetime.fromisoformat(d)
            if not k in redux:
                redux[k] = d
            if d > redux[k]:
                redux[k] = d

        res = []
        [res.append([d.isoformat(),k[0],k[1]]) for k,d in redux.items()]
        res.sort(key=lambda arr:arr[2].lower())
        namemax = max([len(h) for t,i,h in res])
        return [f"{i.ljust(15)} {h.ljust(namemax)}   # {t}" for t,i,h in res]


    def get_hosts(self) -> dict[str,list[str]]:
        """ Retreive all entries in registry

        Returns a map of (ip -> hosts[])
        """
        res = self.select("SELECT ip,hostname FROM Peers;")
        ips = {}
        for ip,hostname in res:
            if ip not in ips:
                ips[ip] = []
            if hostname not in ips[ip]:
                ips[ip].append(hostname)

        return ips


class Sweeper(threading.Thread):
    def __init__(self, dbfile, sweep_interval, age_limit):
        threading.Thread.__init__(self, daemon=True)
        self._dbfile = dbfile
        self._interval = sweep_interval # seconds
        self._limit = age_limit

    def run(self):
        registry = Registry(self._dbfile)
        self.log = GetLog("sweep")

        print(f"Sweeper running every {self._interval} seconds. Purge entries older than {self._limit} seconds.")

        while True:
            try:
                oldest = datetime.datetime.now() - datetime.timedelta(seconds=self._limit)
                registry.sweep(oldest)
            except KeyboardInterrupt:
                raise
            except Exception as e:
                print(f"Error in sweeper: {e}")
                self.log.error(f"Error in sweeper: {e}")
            time.sleep(self._interval)
