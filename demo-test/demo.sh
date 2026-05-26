#!/usr/bin/env bash

THIS="$(realpath "$0")"
HEREDIR="$(dirname "$THIS")"
SCRIPT="$(basename "$0")"

set -euo pipefail

main() {

    case "${1:-}" in
    spin-up)
        name="${2:-fog_default}"
        ip="${3:-192.168.42.0/24}"
        interval=300
        /hostdata/foghorn --log ./${name}.log --database ./demo.${name}.db run ${ip} --interval ${interval} --altname "extraname-${name}"
        ;;
    start)
        cd "$HEREDIR"
        docker compose up -d
        sleep 2
        docker ps | grep demo-test || docker logs demo-test-fog1-1
        
        echo -e "\033[33;1m============ Example of querying a database file for all entries\033[0m"
        (set -x; "$HEREDIR/../foghorn" --database "$HEREDIR/demo.fog1.db" query --dump)
        echo -e "\033[33;1m============ Example of querying a database file for hosts compatible notation\033[0m"
        (set -x; "$HEREDIR/../foghorn" --database "$HEREDIR/demo.fog1.db" query --hosts)
        ;;
    stop)
        cd "$HEREDIR"
        docker compose down
        git clean -dfx "$HEREDIR"
        ;;
    build)
        cd "$HEREDIR"
        docker build ./ -t foghorn:latest
        ;;
    *)
        echo "Unknown - use 'build' 'start' or 'stop'"
        exit 1
        ;;
    esac

}

main "$@"
