""" A simple Config representation class that allows configurations to be loaded from multiple locations,
with higher priority settings overriding lower priority ones.

See loadConfigs() help
"""

import os
import re

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
        assert self._sub is None, f"Sub config is already set from {self._sub._path}"

        self._sub = other

        return self
    

    def get(self, k) -> str:
        v = self._data.get(k)
        if v is None and self._sub:
            v = self._sub.get(k)
        return v
    

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
            conf = Config(path).over(conf)
    return conf


class TestConfig:
    def test_config(self):
        with open("etc-config", 'w') as fh:
            fh.write("PATH=etc\n")
            fh.write("GLOBAL=world\n")
        with open("home-config", 'w') as fh:
            fh.write("PATH=home\n")
            fh.write("SCOPE=home\n")

        conf1 = Config("etc-config")
        conf2 = Config("home-config").over(conf1)

        assert conf2.get("PATH") == "home"
        assert conf2.get("GLOBAL") == "world"
        assert conf2.get("SCOPE") == "home"

        assert conf2.asDict() == {"PATH": "home", "SCOPE":"home", "GLOBAL": "world"}
