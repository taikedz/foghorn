#!/usr/bin/env bash

THIS="$(readlink -f "$0")"
HEREDIR="$(dirname "$THIS")"
PARENTDIR="$(readlink -f "$HEREDIR/..")"

set -euo pipefail

fail() {
    n="$1"; shift
    echo "$*"
    exit $n
}

add_config() {
    mkdir -p /etc/foghorn
    if [[ ! -f /etc/foghorn/config.env ]]; then
        cp "$HEREDIR/config.env.example" /etc/foghorn/config.env
        sed -r -e "s|SERVER_IP=.*|SERVER_IP=${1:-127.0.0.1}|" -i /etc/foghorn/config.env
    fi
}

main() {
    IP="${1:-}"; shift || fail 1 "Specify the network target e.g. '192.168.1.0/24'"

    if [[ "$UID" != 0 ]]; then
        echo "You must be root to run this script"
        exit 1
    fi

    service_file=/etc/systemd/system/foghorn.service

    mkdir -p /var/log/foghorn
    mkdir -p /var/foghorn

    (
        sed -e "s|%COMMAND%|python3 $PARENTDIR/src/foghorn.py --log /var/log/foghorn/foghorn.log run|"
    ) < "$HEREDIR/foghorn.service" > "$service_file"

    add_config "${IP:-}"

    systemctl daemon-reload
    systemctl enable foghorn
    systemctl start foghorn

    echo "Foghorn installed and started. Change configs at /etc/foghorn/config.env"
    echo ""
}


main "$@"
