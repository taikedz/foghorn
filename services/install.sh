#!/usr/bin/env bash

THIS="$(readlink -f "$0")"
HEREDIR="$(dirname "$THIS")"
PARENTDIR="$(readlink -f "$HEREDIR/..")"

fail() {
    n="$1"; shift
    echo "$*"
    exit $n
}

add_config() {
    mkdir -p /etc/foghorn
    if [[ ! -f /etc/foghorn/config.env ]]; then
        cp "$HEREDIR/config.env" /etc/foghorn
    fi
}

main() {
    service_base_path=/etc/systemd/system/foghorn

    action="$1"; shift || fail 1 "No action specified - try 'listener' or 'sender'"

    mkdir -p /var/log/foghorn

    case "$action" in
    listener|server)
        MODE=server
        ACTION=listen
        ;;
    sender|client)
        MODE=client
        ACTION=send
        ;;
    *)
        fail 2 "Unknown action '$action'"
        ;;
    esac

    (
        sed -e "s/%MODE%/$MODE/" -e "s|%COMMAND%|python3 $PARENTDIR/src/foghorn.py --log /var/log/foghorn/foghorn-$MODE.log $ACTION|"
    ) < "$HEREDIR/foghorn.service" > "${service_base_path}-$MODE.service"

    add_config

    systemctl daemon-reload
    systemctl enable "foghorn-$MODE"

    echo "Foghorn $MODE service installed."
    echo "Configure via /etc/foghorn/config.env"
    echo "Start via 'systemctl start foghorn-$MODE'"
}

main "$@"
