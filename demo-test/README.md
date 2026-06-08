# Demo

A quick demo showing multiple hosts starting, pinging eachother on startup, and being immediately available to querying.

Switch into this directory and start the demo. Requires a recent version of docker with `docker compose` subcommand.

```sh
cd demo-test

./demo.sh start
```

The containers will start, each with its own foghorn instance.

On starting, each one will ping out on the subnetwork, causing any existing ones, including earlier ones, to respond.

You can demonstrate the host content by querying the particular demo database, e.g.

```sh
./demo.sh query demo.fog1.db
```

Tear down and cleanup the demo with

```sh
./demo.sh stop
```