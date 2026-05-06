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
    if [[ "$UID" != 0 ]]; then
        echo "You must be root to run this script"
        exit 1
    fi

    service_base_path=/etc/systemd/system/foghorn

    action="${1:-}"; shift || fail 1 "No action specified - try 'listener' or 'sender'"

    mkdir -p /var/log/foghorn
    mkdir -p /var/foghorn

    case "$action" in
    listener|server)
        MODE=server
        ACTION=listen
        ;;
    sender|client)
        MODE=client
        ACTION=send
        IP="${1:-}"; shift || fail 1 "Specify the IP of the listener server."
        ;;
    *)
        fail 2 "Unknown action '$action'"
        ;;
    esac

    (
        sed -e "s/%MODE%/$MODE/" -e "s|%COMMAND%|python3 $PARENTDIR/src/foghorn.py --log /var/log/foghorn/foghorn-$MODE.log $ACTION|"
    ) < "$HEREDIR/foghorn.service" > "${service_base_path}-$MODE.service"

    add_config "$IP"

    systemctl daemon-reload
    systemctl enable "foghorn-$MODE"
    systemctl start "foghorn-$MODE"

    echo "Foghorn $MODE installed and started. Change configs at /etc/foghorn/config.env"
    echo ""
}


main "$@"
