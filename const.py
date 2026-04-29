from config import loadConfigs


defvals = {
    "port": 62001
}

CONFIG = loadConfigs([
    "/etc/foghorn/settings.env",
    "~/.config/foghorn/settings.env",
    "./foghorn-config.env",
], defaults=defvals)

MINUTES = 60
