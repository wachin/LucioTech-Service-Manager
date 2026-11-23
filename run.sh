#!/usr/bin/env bash
# Arranca LucioTech Service Manager con el entorno virtual del proyecto.
set -euo pipefail

project_dir="$(cd -- "$(dirname -- "${BASH_SOURCE[0]}")" && pwd)"
python="$project_dir/.venv/bin/python"

if [[ ! -x "$python" ]]; then
    echo "No se encontró el intérprete $python" >&2
    echo "Crea el entorno con:" >&2
    echo "  python3 -m venv .venv" >&2
    echo "  .venv/bin/python -m pip install -r requirements.txt" >&2
    exit 1
fi

export PYTHONPATH="$project_dir/src${PYTHONPATH:+:$PYTHONPATH}"
exec "$python" -m luciotech.main "$@"
