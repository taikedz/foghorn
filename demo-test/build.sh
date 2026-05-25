#!/usr/bin/env bash

THIS="$(realpath "$0")"
HEREDIR="$(dirname "$THIS")"
SCRIPT="$(basename "$0")"

set -euo pipefail

main() {
    docker build "$HEREDIR" -t foghorn
}

main "$@"
