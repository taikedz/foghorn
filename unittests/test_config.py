from io import TextIOWrapper
import os

from src.config import Config


class Tmpfile:
    def __init__(self, path, mode):
        self._p = path
        self._m = mode
        self._fh:TextIOWrapper = None
    
    def __enter__(self):
        self._fh = open(self._p, self._m)
        return self._fh


    def __exit__(self, *e):
        self._fh.close()
        os.remove(self._p)


class TestConfig:
    def test_config(self):
        with Tmpfile("etc-config.env", 'w') as fh1, Tmpfile("home-config.env", 'w') as fh2:
            fh1.write("PATH=etc\n")
            fh1.write("GLOBAL=world\n")
            fh2.write("PATH=home\n")
            fh2.write("SCOPE=home\n")
            fh1.flush()
            fh2.flush()

            conf1 = Config("etc-config.env")
            conf2 = Config("home-config.env").over(conf1)

            assert conf2.get("PATH") == "home"
            assert conf2.get("GLOBAL") == "world"
            assert conf2.get("SCOPE") == "home"

            assert conf2.asDict() == {"PATH": "home", "SCOPE":"home", "GLOBAL": "world"}

            assert conf2.get("GLOBAL", "oops") == "world"
            assert conf2.get("SCOPE", "oops") == "home"
            assert conf2.get("UNKNOWN", "oops") == "oops"
