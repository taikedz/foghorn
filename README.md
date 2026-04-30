# Foghorn

A blunt beacon that announces its presence.

For when you're not IT and you need a poor-sod's host discovery.

A troubleshooting tool, put it on all machines, and find misconfigured IPs and hostnames.

## Send and listen

Run `foghorn.py listen` to listen for any packets from a foghorn sender.

Run `foghorn.py send 192.168.3.15` to send packets to a server listening at the specified IP.

Run `foghorn.py send -B 192.168.3.255` to broadcast on the `192.168.3.0/24` subnetwork such that all listeners will receive. Note that some organisations block chatter on broadcast addresses.

Automatically cleans up old entries in the peers database older than a given amount of time - default 30 minutes.

## Query

Query the history of machines that have been reporting in:

* for a name, see all IPs that claim to be that name : `foghorn.py query --host testvm1`
* for an IP, see all the names that claim to have that IP : `foghorn.py query --ip 192.168.3.3`
* show everything : `foghorn.py query --dump`

## Configs

A home config at `~/.config/foghorn/config.env` or local `./foghorn-config.env` can be specified. Local config overrides any settings in home config. Home config overrides global `/etc/foghorn/config.env` if it exists.

Config keys currently available are `SERVER_IP` (client's `ip` argument) and `BIND` (listener's `--bind` option)

## Service

Run `bash services/install.sh {client|server}` to install either of a client (sender) or a server (listener).

These must then be configured at `/etc/foghorn/config.env`