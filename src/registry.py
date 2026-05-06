import os
import time
import sqlite3
import datetime
import threading
from typing import Callable

from foglog import GetLog

class Registry:
    # All instances will share this lock, this is intentional.
    #  It seems sqlite connections do _not_ multithread, so we
    #  need to prevent different registry instances from colliding.
    REGISTRY_LOCK = threading.RLock()

    def __init__(self, dbfile:str):
        self.log = GetLog("registry")
        self.log.info(f"Using database file {repr(dbfile)}")
        self._dbfile = dbfile

        exists = os.path.exists(self._dbfile)

        if not exists:
            self.log.info("Creating new tables")
            self.execute("""
                CREATE TABLE Peers (
                        id INTEGER PRIMARY KEY,
                        hostname STRING,
                        ip STRING,
                        seen DATETIME
                        );
                        """)


    def execute(self, command, holders=()):
        with self.REGISTRY_LOCK, sqlite3.connect(self._dbfile) as dbconn:
            cursor = dbconn.cursor()
            cursor.execute(command, holders)
            dbconn.commit()


    def select(self, command, holders=()) -> list[list]:
        with self.REGISTRY_LOCK, sqlite3.connect(self._dbfile) as dbconn:
            cursor = dbconn.cursor()
            cursor.execute(command, holders)
            rows = cursor.fetchall()
            dbconn.commit()
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
        self.log.debug(f"Removing {len(rmpeers)} stale entries.")
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
        res = sort_rows(res, organise_on=2, sort_on=(0, datetime.datetime.fromisoformat) )
        print("\n".join( [f"{i.ljust(15)} {h.ljust(20)}   # {t}" for t,i,h in res] )
        )


    def latest_pairs(self):
        res = self.select("SELECT seen,ip,hostname FROM Peers;")
        res = sort_rows(res, organise_on=2, sort_on=(0, datetime.datetime.fromisoformat) )

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

        print("\n".join( [f"{i.ljust(15)} {h.ljust(20)}   # {t}" for t,i,h in res] )
        )


    def get_hosts(self) -> dict[str,list[str]]:
        """ Print all entries
        """
        res = self.select("SELECT ip,hostname FROM Peers;")
        ips = {}
        for ip,hostname in res:
            if ip not in ips:
                ips[ip] = []
            if hostname not in ips[ip]:
                ips[ip].append(hostname)

        return ips


    def print_hosts(self):
        ips = self.get_hosts()
        for ip, hostlist in ips.items():
            print(f"{ip}  {' '.join(hostlist)}")


def sort_rows(rows:list[list], organise_on:int, sort_on:tuple[int,Callable]) -> list[list]:
    groupings:dict[str,list] = {}
    for items in rows:
        k = items[organise_on]
        if groupings.get(k) is None:
            groupings[k] = []
        groupings[k].append(items[:])

    end_list = []
    sort_idx, sort_type = sort_on
    for items_list in groupings.values():
        items_list.sort(key=lambda item: sort_type(item[sort_idx]))
        end_list.extend(items_list)

    return end_list


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