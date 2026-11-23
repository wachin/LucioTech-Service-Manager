#!/usr/bin/env bash
# Actualiza los catálogos de traducción (§21).
#
# 1. Extrae con pylupdate6 los textos de las llamadas tr()/translate() del código.
# 2. Compila cada translations/*.ts a src/luciotech/ui/translations/*.qm con lrelease.
#
# Los .ts se revisan y se completan en Qt Linguist. El inglés no necesita archivo: es el
# idioma fuente del código.
set -euo pipefail

project_dir="$(cd "$(dirname "${BASH_SOURCE[0]}")/.." && pwd)"
cd "$project_dir"

if [[ -x .venv/bin/pylupdate6 ]]; then
    pylupdate6=.venv/bin/pylupdate6
else
    pylupdate6=pylupdate6
fi
lrelease="${LRELEASE:-lrelease}"
mkdir -p src/luciotech/ui/translations

mapfile -d '' sources < <(find src/luciotech -name '*.py' -print0)
for ts in translations/*.ts; do
    [[ -e "$ts" ]] || continue
    "$pylupdate6" "${sources[@]}" -ts "$ts"
    "$lrelease" "$ts" -qm "src/luciotech/ui/translations/$(basename "${ts%.ts}").qm"
done
