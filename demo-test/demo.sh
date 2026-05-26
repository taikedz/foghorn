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
        /hostdata/foghorn --log ./${name}.log --database ./demo.${name}.db run ${ip} --interval ${interval}
        ;;
    demo)
        cd "$HEREDIR"
        docker compose down
        docker compose up -d
        sleep 2
        docker ps | grep demo-test || docker logs demo-test-fog1-1
        ;;
    stop)
        cd "$HEREDIR"
        docker compose down
        ;;
    build)
        cd "$HEREDIR"
        docker build ./ -t foghorn:latest
        ;;
    *)
        echo "Unknown - use 'build' or 'demo'"
        exit 1
        ;;
    esac

}

main "$@"
