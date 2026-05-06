# Foghorn

A blunt beacon that announces its presence.

For when you're not IT and you need a poor-sod's host discovery.

A troubleshooting tool, put it on all machines, and find misconfigured IPs and hostnames.

There is no TLS or authentication. NOT FOR USE ON THE INTERNET OR UNTRUSTED NETWORKS.

## Quick Start

If you want to quickly serve:

```sh
# Create a defaul foghorn listener
sudo services/install.sh server
```

A server will start, with default configurations. See `/etc/foghorn/config.env`

If you want to quickly set up a client beacon to talk to a server:

```sh
# Use the IP of the server where you set up a foghorn listener.
sudo services/install.sh client 192.168.19.5
```

(If you do not have `sudo` access on the machines, directly run `python3 src/foghorn.py --help` for how to run it manually)

To find out what the listener has seen:

```sh
# Replace the IP with the one of the listener server
curl http://192.168.19.5:35080/
```


# Details

## Send and listen

Run `foghorn.py listen` to listen for any packets from a foghorn sender.

Run `foghorn.py send 192.168.3.15` to send packets to a server listening at the specified IP.

Run `foghorn.py send -B 192.168.3.255` to broadcast on the `192.168.3.0/24` subnetwork such that all listeners will receive. Note that some organisations block chatter on broadcast addresses.

Automatically cleans up old entries in the peers database older than a given amount of time - default 30 minutes.

## Query

Query the history of machines that have been reporting in for a given database:

* for a name, see all IPs that claim to be that name : `foghorn.py --database path/to/database.db query --host testvm1`
* for an IP, see all the names that claim to have that IP : `foghorn.py --database path/to/database.db query --ip 192.168.3.3`
* show everything : `foghorn.py --database path/to/database.db query --dump`

You can set `DATABASE=` in a local `./foghorn-config.env` to avoid including the long path every time.

## Configs

A home config at `~/.config/foghorn/config.env` or local `./foghorn-config.env` can be specified. Local config overrides any settings in home config. Home config overrides global `/etc/foghorn/config.env` if it exists.

See `services/config.env.example`

## Service

Run `bash services/install.sh { server | client <ip> }` to install either of a client (sender) or a server (listener).

These can then be further configured at `/etc/foghorn/config.env`. If you change configurations, you need to `sudo systemctl restart foghorn-client` or `foghorn-server` as appropriate.

# License

Foghorn is covered by the LGPLv3 license, (C) Tai Kedzierski

You may include it in proprietary solutions.
