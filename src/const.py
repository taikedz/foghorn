from config import loadConfigs


defvals = {
    "PORT": 62001,
    "DATABASE": "peers.sqlite",
}

CONFIG = loadConfigs([
    "/etc/foghorn/config.env",
    "~/.config/foghorn/config.env",
    "./foghorn-config.env",
], defaults=defvals)

MINUTES = 60
