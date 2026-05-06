""" A simple Config representation class that allows configurations to be loaded from multiple locations,
with higher priority settings overriding lower priority ones.

See loadConfigs() help
"""

import os
import re

from util import asBool

class Config:
    def __init__(self, source:str|dict|None):
        self._sub = None

        if source is None:
            self._path = "<none>"
            self._data = {}
            return
        elif isinstance(source, dict):
            self._path = "<inline>"
            self._data = source
            return
        else:
            self._path = source
            self._data = {}

        with open(self._path) as fh:
            for line in fh.readlines():
                line = re.sub(r'#.*$', '', line)
                line = line.strip()
                if line:
                    assert "=" in line, f"Invalid config line: {repr(line)}"
                    k,v = line.split('=', maxsplit=1)
                    k = k.strip()
                    self._data[k] = v


    def over(self, other:'Config|None') -> 'Config':
        """ Use current configuration with precedence over the config supplied as argument.

        Current config's values will be used, undefined keys will be deferred to `other` config.
        """
        assert self._sub is None, f"Sub config is already set from {self._sub._path}"

        self._sub = other

        return self
    

    def under(self, other_data:dict) -> 'Config':
        """ Use the data supplied in argument as a high precedence config,
        with current config having lower precedence.

        In the resulting config, `other_data`'s config values will be used, undefined keys will
        be deferred to this original config.
        """
        cf = Config(other_data)
        return cf.over(self)
    

    def get(self, k, default=None) -> str|None:
        v = self._data.get(k)
        if v is None and self._sub:
            v = self._sub.get(k)
        if v is None:
            v = default
        return v

    def getBool(self, k) -> bool:
        return asBool(self.get(k, "false"))


    def getInt(self, k, default=-1) -> int:
        v = self.get(k)
        if v is None:
            raise ValueError(f"Setting '{k}' is not populated.")
        return int(v)
    

    def asDict(self) -> dict:
        if not self._sub is None:
            vals = self._sub.asDict()
        else:
            vals = {}
        vals.update(self._data)
        return vals


def loadConfigs(paths:list[str], defaults:dict|None = None) -> Config:
    """ Load configs from least precedence to most precedence.

    ```python
    loadConfigs([
        "/etc/my-config",
        "~/.config/my-config",
        "./my-app.config",
    ], defaults={"SETTING": "default-value"})
    ```

    Configurations are loaded from the global space; overrides from the home space are loaded over that, and
    overrides from the current directory are loaded above that in turn.
    """
    conf = Config(defaults)
    for path in paths:
        path = os.path.expanduser(path)
        if os.path.exists(path):
            print(f"Loading config from {path}")
            conf = Config(path).over(conf)
    return conf


class TestConfig:
    def test_config(self):
        with open("etc-config.env", 'w') as fh:
            fh.write("PATH=etc\n")
            fh.write("GLOBAL=world\n")
        with open("home-config.env", 'w') as fh:
            fh.write("PATH=home\n")
            fh.write("SCOPE=home\n")

        conf1 = Config("etc-config.env")
        conf2 = Config("home-config.env").over(conf1)

        assert conf2.get("PATH") == "home"
        assert conf2.get("GLOBAL") == "world"
        assert conf2.get("SCOPE") == "home"

        assert conf2.asDict() == {"PATH": "home", "SCOPE":"home", "GLOBAL": "world"}

        assert conf2.get("GLOBAL", "oops") == "world"
        assert conf2.get("SCOPE", "oops") == "home"
        assert conf2.get("UNKNOWN", "oops") == "oops"
