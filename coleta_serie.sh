#!/usr/bin/env bash
# Coleta os artefatos pequenos de uma serie para dentro do repositorio do TCC,
# e registra o manifesto de hashes dos artefatos grandes.
#
# Politica de retencao — pre-registro §7:
#   - JSONs e logs vao para o git (registro citavel)
#   - .ply e renders ficam em disco/nuvem, com hash versionado aqui
#
# Uso: bash coleta_serie.sh <D0|D1|D2|D3>

set -euo pipefail

DEGREE="${1:?uso: coleta_serie.sh <D0|D1|D2|D3>}"
SRC="$HOME/tcc-runs/series/$DEGREE"
DST="$HOME/code/tcc/pivo-reprodutibilidade-3dgs/dados/$DEGREE"

[ -d "$SRC" ] || { echo "ABORTA: $SRC nao existe" >&2; exit 1; }
mkdir -p "$DST"

MANIFEST="$DST/manifest.tsv"
printf 'run\tarquivo\tbytes\tsha256\n' > "$MANIFEST"

N=0
for RD in "$SRC"/run*/; do
  RUN="$(basename "$RD")"
  OUT="$DST/$RUN"
  mkdir -p "$OUT"

  if [ -f "$RD/env.json" ]; then
    cp "$RD/env.json" "$OUT/"
  else
    echo "AVISO: $RUN sem env.json" >&2
  fi

  for TD in "$RD"*/; do
    [ -d "$TD" ] || continue
    for f in config.json train.json eval.json; do
      [ -f "$TD$f" ] && cp "$TD$f" "$OUT/"
    done
    printf '%s\n' "$TD" > "$OUT/origem.txt"

    if [ -f "$TD/splat.ply" ]; then
      SZ="$(stat -c%s "$TD/splat.ply")"
      SH="$(sha256sum "$TD/splat.ply" | cut -d' ' -f1)"
      printf '%s\tsplat.ply\t%s\t%s\n' "$RUN" "$SZ" "$SH" >> "$MANIFEST"
    fi

    NPNG="$(find "$TD" -maxdepth 1 -name 'val_*.png' | wc -l)"
    PNGSZ="$(du -sb "$TD" | cut -f1)"
    printf '%s\tval_png_count\t%s\t-\n' "$RUN" "$NPNG" >> "$MANIFEST"
    printf '%s\tdir_total_bytes\t%s\t-\n' "$RUN" "$PNGSZ" >> "$MANIFEST"
  done

  # log bruto: preservado sem filtragem (contem escapes ANSI de proposito)
  [ -f "$SRC/logs/$RUN.log" ] && cp "$SRC/logs/$RUN.log" "$OUT/"

  N=$((N + 1))
done

[ -f "$SRC/logs/build.log" ] && cp "$SRC/logs/build.log" "$DST/"

echo "coletadas $N execucoes de $DEGREE para $DST"
echo "manifesto: $MANIFEST"
du -sh "$DST"
