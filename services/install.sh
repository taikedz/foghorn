#!/usr/bin/env bash

THIS="$(readlink -f "$0")"
HEREDIR="$(dirname "$THIS")"
PARENTDIR="$(readlink -f "$HEREDIR/..")"

CONFIG_FILE=/etc/foghorn/config.env

set -euo pipefail

fail() {
    n="$1"; shift
    echo "$*"
    exit $n
}

add_config() {
    if [[ ! -f "$CONFIG_FILE" ]]; then
        cp "$HEREDIR/config.env.example" "$CONFIG_FILE"
    fi

    if [[ -n "${1:-}" ]]; then
        sed -r -e "s|SERVER_IP=.*|SERVER_IP=${1}|" -i "$CONFIG_FILE"
    fi

    if [[ -n "${2:-}" ]]; then
        sed -r -e "s|ALTNAME=.*|ALTNAME=${2}|" -i "$CONFIG_FILE"
    fi
}

main() {
    IP="${1:-}"; shift || {
        if [[ ! -f "$CONFIG_FILE" ]]; then
            fail 1 "Specify the network target e.g. '192.168.1.0/24'"
        fi
    }

    if [[ "$UID" != 0 ]]; then
        echo "You must be root to run this script"
        exit 1
    fi

    service_file=/etc/systemd/system/foghorn.service

    mkdir -p /var/log/foghorn
    mkdir -p /var/foghorn
    mkdir -p /etc/foghorn

    (
        sed -e "s|%COMMAND%|python3 $PARENTDIR/src/foghorn.py --log /var/log/foghorn/foghorn.log run|"
    ) < "$HEREDIR/foghorn.service" > "$service_file"

    add_config "${IP:-}"

    systemctl daemon-reload
    systemctl enable foghorn
    systemctl restart foghorn

    echo "Foghorn installed and started. Change configs at /etc/foghorn/config.env"
    echo "Ensure your firewall is allowing $(grep "PORT=" "$CONFIG_FILE") on UDP"
    echo ""
}


main "$@"
