# Foghorn

A blunt beacon that announces its presence.

For when you're not IT and you need a poor-sod's host discovery.

A troubleshooting tool, put it on all machines, and find misconfigured IPs and hostnames.

There is no TLS or authentication. NOT FOR USE ON THE INTERNET OR UNTRUSTED NETWORKS.

## Quick Start

### Server

```sh
# Create a defaul foghorn listener
sudo services/install.sh server
```

A server will start, with default configurations. See `/etc/foghorn/config.env`

### Client

#### You have sudo access - install daemon

```sh
# Use the IP of the server where you set up a foghorn listener.
sudo services/install.sh client 192.168.19.5
```

If your client host has a mandatory generic hostname but you want it to broadcast a more suited name, set `ALTNAME=` in the `/etc/foghorn/config.env` file

#### You do not have sudo access - run from CLI

```sh
# Use the IP of the server where you set up a foghorn listener.
# You can optionally include `--altname myserver` to report an alternative name for your machine,
#   the registry will show it as an entry titled `alt.myserver`
python3 src/foghorn.py 192.168.19.5 --altname myserver
```

### Query

If the listener has been started with an outward-facing HTTP server (use configuration `ETC_HOSTS_SERVER=<ip>` (replacing with your actual IP) or `--etc-hosts-server`) , you can use curl to ask for a dump of entries:

Ask the server owner for the required access token:

```sh
# Replace the IP with the one of the listener server
curl "http://<ip>:35080/?token=<token>"
```

Otherwise, SSH to the server, and run `foghorn.py --database /path/to/db/file query --latest`.

# Details

## Send and listen

**Listener**

Run `foghorn.py listen` to listen for any packets from a foghorn sender.

When run with `--sweep true`, foghorn cleans up old entries in the peers database older than a given amount of time - default 30 minutes.

When `--etc-hosts-server 0.0.0.0` is supplied, a HTTP endpoint is enabled to return an `/etc/hosts` compatible listing of all hosts that have reported in. It _requires_ a token to be supplied in arguments, e.g. `curl http://<ip>/?token=<token>` . The token is renewed at each launch of the listener and stored to a file. See your config's `TOKEN_FILE` setting to determine the path.

**Client**

Run `foghorn.py send 192.168.3.15` to send packets to a server listening at the specified IP.

Run `foghorn.py send 192.168.3.15 --interval 300` to send packets to a server listening at the specified IP every 300 seconds (which is 5 minutes).

Run `foghorn.py send -B 192.168.3.255` to broadcast on the `192.168.3.0/24` subnetwork such that all listeners will receive. Note that some organisations block chatter on broadcast addresses.

Your machine may have a corporate mandatory name like `unit4567-corp` ; if you want to report a custom name run as `foghorn.py send 192.168.3.15 --altname=chat-server` . The listener will then additionally register a machine named `alt.chat-server`, which will be returned in queries.

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
