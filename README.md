# Foghorn

A blunt beacon that announces its presence.

A troubleshooting tool, put it on all machines, and find misconfigured IPs and hostnames.

# Send and listen

Run `foghorn.py listen -B all` to listen for broadcast packets from a foghorn sender.

Run `foghorn.py send -B 192.168.3.255` to broadcast on the `192/168/3.0/24` subnetwork such that all listeners will receive.

# Query

Query the history of machines that have been reporting in:

* for a name, see all IPs that claim to be that name
* for an IP, see all the names that claim to have that IP
