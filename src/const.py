from config import loadConfigs


defvals = {
    "PORT": 35053,
    "DATABASE": "peers.sqlite",
    "HTTP_PORT": 35080,
    "SWEEP": "false",
    "ETC_HOSTS_SERVER": "false"
}

CONFIG = loadConfigs([
    "/etc/foghorn/config.env",
    "~/.config/foghorn/config.env",
    "./foghorn-config.env",
], defaults=defvals)

MINUTES = 60
