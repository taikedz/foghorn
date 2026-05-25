# Foghorn

A blunt beacon that announces its presence.

For when you're not IT and you need a poor-sod's host discovery.

A troubleshooting tool, put it on all machines, and find misconfigured IPs and hostnames.

There is no TLS or authentication. NOT FOR USE ON THE INTERNET OR UNTRUSTED NETWORKS.

## Quick Start

### With sudo access

```sh
# Create a default foghorn service which will ping the full subnetwork specified every 5 minutes
sudo services/install.sh 192.168.42.0/24
```

A server will start listening, with default configurations. It will also periodically send out a ping every 5 minutes to each individual address on the specified subnet.

Instead of a subnet, you can also specify a single IP.

See `/etc/foghorn/config.env` for further options. After adjusting configurations, run `sudo systemctl restart foghorn`

### Sudo-less

If you do not have sudo on your machine, you can simply run foghon as a regular user process

```sh
# You can optionally include `--altname myserver` to report an alternative name for your machine,
#   the registry will show it as an entry titled `alt.myserver`
python3 src/foghorn.py 192.168.42.0/24 --altname myserver
```

### Query

Any machine running foghorn can query its local database. It is recommended to run each client such that it pings a specified subnetwork, so that all machines involved can mutually discover.

To query your instance's registry run `foghorn.py [--database </path/to/db/file>] query --hosts`

This will dump the peers that have reported in along with their altnames, in a hosts-file compatible notaiton.

So long as the database is set in `/etc/foghorn/config.env`, you may omit the `--database DATABASE` option, as the running service honours the global config.

# Details

## Send and listen

Foghorn implements a sender process, and a listener process

**Listener** (server)

Listener listens on the specified bin addres (defaulting to 0.0.0.0 which listens on all interfaces).

When run with `--sweep true`, foghorn cleans up old entries in the peers database older than a given amount of time - default 30 minutes, specifed by `--sweep-interval`.


**Sender** (client)

The IP/network specified tells the sender component where to send pings to. It can either be a single IP, or a subnet specifed by CIDR notation

Other arguments supplied control additional aspects

Args examples

* `192.168.3.15` to send packets to a host listening at the specified IP.
* `192.168.3.0/24 --interval 300` to send packets to all hosts in the specified range, every 300 seconds (which is 5 minutes).

Your machine may have a corporate mandatory name like `unit4567-corp` ; if you want to report a custom name run as `foghorn.py 192.168.3.15 --altname=chat-server` . The listener will then additionally register a machine named `alt.chat-server`, which will be returned in queries.

## Query

Query the history of machines that have been reporting in for a given database:

* for a name, see all IPs that claim to be that name : `foghorn.py --database path/to/database.db query --host testvm1`
* for an IP, see all the names that claim to have that IP : `foghorn.py --database path/to/database.db query --ip 192.168.3.3`
* show everything : `foghorn.py --database path/to/database.db query --dump`

You can set `DATABASE=` in a local `./foghorn-config.env` to avoid including the long path every time, or set it globally in `/etc/foghorn/config.env`

## Configs

A home config at `~/.config/foghorn/config.env` or local `./foghorn-config.env` can be specified. Local config overrides any settings in home config. Home config overrides global `/etc/foghorn/config.env` if it exists.

See `services/config.env.example`

## Service

Run `bash services/install.sh <ip>` to install foghorn as a service in systemd.

This can then be further configured at `/etc/foghorn/config.env`. If you change configurations, you need to `sudo systemctl restart foghorn`

# License

Foghorn is covered by the LGPLv3 license, (C) Tai Kedzierski

You may include it in proprietary solutions.

But you really should not. It is not fit for customer production use. **It is an internal ops tool**.
