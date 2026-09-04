#!/usr/bin/env bash
set -euo pipefail
DEGREE="${1:?uso: run_degree.sh <D0|D1|D2|D3> <N>}"
N="${2:?}"
FORK="$HOME/code/vksplatTCC"

cd "$FORK"
git diff --quiet || { echo "ABORTA: arvore suja no fork" >&2; exit 1; }
git checkout "$DEGREE"
echo "--- HEAD: $(git rev-parse HEAD)"

cd "$FORK/vksplat"
echo "--- recompilando (incondicional)"
pip install -e . --no-build-isolation > /tmp/build_$DEGREE.log 2>&1 \
  || { echo "ABORTA: falha de build, ver /tmp/build_$DEGREE.log" >&2; exit 1; }

cd "$FORK"
bash run_series.sh "$DEGREE" "$N"