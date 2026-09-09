#!/usr/bin/env bash
# Orquestrador de série do experimento de reprodutibilidade em 3DGS.
#
# Vive no repositório do TCC, NÃO no fork do VkSplat: é camada acima da escada
# de ablação e não pertence ao estado de código de nenhum degrau. Ver
# pivo-reprodutibilidade-3dgs/pre-registro.md §3.2.
#
# Uso:  bash run_degree.sh <D0|D1|D2|D3> <indice_inicial> <indice_final>
# Ex.:  bash run_degree.sh D0 0 9      # primeira janela de 10
#       bash run_degree.sh D0 10 19    # continuação, se o CI não fechar
#
# Responsabilidades:
#   1. recusar árvore suja no fork          (pré-registro §9)
#   2. recusar reutilização de índice       (protege a proveniência)
#   3. checkout do degrau por tag
#   4. RECOMPILAR INCONDICIONALMENTE        (pré-registro §3.2 — o .so não é
#      versionado, logo checkout não troca o binário; este é o modo de falha
#      silencioso do protocolo)
#   5. rodar a série com saída ao vivo e log em arquivo
#   6. aplicar os critérios de invalidação  (pré-registro §9)

set -euo pipefail

DEGREE="${1:?uso: run_degree.sh <D0|D1|D2|D3> <inicio> <fim>}"
FIRST="${2:?falta indice inicial}"
LAST="${3:?falta indice final}"

FORK="$HOME/code/vksplatTCC"
OUT_ROOT="$HOME/tcc-runs/series"
LOGS="$OUT_ROOT/$DEGREE/logs"

mkdir -p "$LOGS"

# --- 2. indices nao sao reutilizaveis ---------------------------------------
for i in $(seq "$FIRST" "$LAST"); do
  D="$OUT_ROOT/$DEGREE/run$(printf '%03d' "$i")"
  if [ -e "$D" ]; then
    echo "ABORTA: $D ja existe. Indices nao sao reutilizaveis." >&2
    echo "        Mova ou remova a serie anterior, ou use outro intervalo." >&2
    exit 1
  fi
done

# --- 1 e 3. estado do fork --------------------------------------------------
cd "$FORK"
git diff --quiet || { echo "ABORTA: arvore suja no fork ($FORK)" >&2; exit 1; }
git checkout --quiet "$DEGREE"
SHA="$(git rev-parse HEAD)"

echo "=========================================================="
echo " degrau    : $DEGREE"
echo " commit    : $SHA"
echo " execucoes : $FIRST a $LAST"
echo " saida     : $OUT_ROOT/$DEGREE"
echo " inicio    : $(date -Is)"
echo "=========================================================="

# --- 4. rebuild incondicional ----------------------------------------------
echo "[$(date +%H:%M:%S)] recompilando (incondicional)..."
cd "$FORK/vksplat"
if ! pip install -e . --no-build-isolation > "$LOGS/build.log" 2>&1; then
  echo "ABORTA: falha de build. Ver $LOGS/build.log" >&2
  exit 1
fi
echo "[$(date +%H:%M:%S)] build ok"

# --- 5 e 6. serie -----------------------------------------------------------
T_SERIE=$(date +%s)
DONE=0

for i in $(seq "$FIRST" "$LAST"); do
  IDX="$(printf '%03d' "$i")"
  L="$LOGS/run$IDX.log"
  T0=$(date +%s)

  echo
  echo "---------- $DEGREE run $IDX (ate $LAST)   [$(date +%H:%M:%S)] ----------"

  # stdbuf + python -u: evita que a saida fique presa no buffer do pipe
  if ! stdbuf -oL -eL python -u tcc_runner.py "$i" "$OUT_ROOT" "$DEGREE" 2>&1 | tee "$L"; then
    echo "ABORTA: execucao $IDX falhou (exit != 0). Ver $L" >&2
    exit 1
  fi

  # criterios de invalidacao — pre-registro §9.
  # -F trata o padrao como texto literal: dispensa escape e e imune a perda
  # de barra invertida em copia/colagem.
  grep -qF 'Using device [0]' "$L" \
    || { echo "ABORTA: dispositivo inesperado em $L" >&2; exit 1; }
  grep -qF 'RX 9070 XT (RADV GFX1201) - VIABLE' "$L" \
    || { echo "ABORTA: GPU esperada nao enumerada em $L" >&2; exit 1; }
  ! grep -qiF 'USE_EMULATED' "$L" \
    || { echo "ABORTA: caminho emulado acionado em $L" >&2; exit 1; }

  DONE=$((DONE + 1))
  DT=$(( $(date +%s) - T0 ))
  MED=$(( ($(date +%s) - T_SERIE) / DONE ))
  REST=$(( MED * (LAST - i) ))
  printf '>>> run %s ok em %dm%02ds | media %dm%02ds | restante ~%dh%02dm\n' \
    "$IDX" $((DT/60)) $((DT%60)) $((MED/60)) $((MED%60)) \
    $((REST/3600)) $(((REST%3600)/60))
done

echo
echo "=========================================================="
echo " $DEGREE runs $FIRST..$LAST concluidos"
echo " tempo total: $(( ($(date +%s) - T_SERIE) / 60 )) min"
echo " commit     : $SHA"
echo " fim        : $(date -Is)"
echo "=========================================================="
