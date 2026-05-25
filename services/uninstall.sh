#!/usr/bin/env bash

blat() {
    echo -n "Uninstalling foghorn $1 - "
    if [[ -f /etc/systemd/system/foghorn$1.service ]]; then
        systemctl stop foghorn$1
        systemctl disable foghorn$1
        rm /etc/systemd/system/foghorn$1.service
        echo "removed."
    else
        echo "not present."
    fi
}

if [[ "$UID" != 0 ]]; then
    echo "You must be root to run this script"
    exit 1
fi

blat -client
blat -server
blat ""

echo "Done."