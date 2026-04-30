from config import loadConfigs


defvals = {
    "port": 62001
}

CONFIG = loadConfigs([
    "/etc/foghorn/config.env",
    "~/.config/foghorn/config.env",
    "./foghorn-config.env",
], defaults=defvals)

MINUTES = 60
