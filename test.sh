THIS="$(readlink -f "$0")"
HEREDIR="$(dirname "$THIS")"

VENVDIR="$HEREDIR/.venv"

activate() { source "$VENVDIR/bin/activate"; }

if [[ ! -d "$VENVDIR" ]]; then
    python3 -m venv "$VENVDIR"
    echo '*' > "$VENVDIR/.gitignore"
    (activate; pip install -r "$HEREDIR/requirements.txt") || exit 1
fi

activate

set -e

export PYTHONPATH="$HEREDIR:$HEREDIR/src"

lizard ./src
pytest ./unittests
