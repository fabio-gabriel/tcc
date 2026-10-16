#!/usr/bin/env bash
# Orquestrador da serie H3b (pre-registro.md §6 e §11.14). COPIA de
# run_degree.sh, com tres diferencas e nenhuma outra:
#   1. checkout da tag D4b (fixa), saida em series/H3b/;
#   2. o executor e experimentos/executar_h3b.py (perturbacao de um bit antes do
#      passo 0), e nao vksplat/tcc_runner.py;
#   3. checagem extra por execucao: env.json com "verificado": true.
# Snapshot de ambiente, rebuild incondicional e criterios do §9: identicos.
# run_degree.sh NAO foi alterado.
#
# Uso:  bash run_h3b.sh <indice_inicial> <indice_final>     # ex.: 0 9

set -euo pipefail

DEGREE="H3b"
TAG="D4b"
FIRST="${1:?uso: run_h3b.sh <inicio> <fim>}"
LAST="${2:?falta indice final}"
TCC="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
RUNNER="$TCC/experimentos/executar_h3b.py"
[ -f "$RUNNER" ] || { echo "ABORTA: $RUNNER nao existe" >&2; exit 1; }

FORK="$HOME/code/vksplatTCC"
OUT_ROOT="$HOME/tcc-runs/series"
LOGS="$OUT_ROOT/$DEGREE/logs"

mkdir -p "$LOGS"

# --- 0. captura de ambiente de userspace ------------------------------------
# Acrescentado em 2026-09-21. Motivo: auditoria dos dados em disco descobriu
# que os dois blocos de D3 correram sob kernels diferentes (7.0.0-30 nos runs
# 000-009, 7.0.0-31 nos runs 010-019) e que o env.json do tcc_runner.py NAO
# registra a versao de Mesa/RADV. Num trabalho sobre reprodutibilidade
# numerica isso e lacuna de primeira ordem: o RADV e o compilador de SPIR-V
# para ISA, logo a versao do Mesa e potencialmente mais determinante do
# resultado numerico que a versao do kernel.
#
# POR QUE ISTO VIVE AQUI, E NAO NO tcc_runner.py:
#   O tcc_runner.py esta no fork e dentro dos commits/tags dos degraus.
#   Edita-lo teria dois efeitos inaceitaveis: (a) sujaria a arvore do fork,
#   fazendo este proprio script abortar na checagem de §9 na linha abaixo; e
#   (b) alteraria os SHAs registrados em pre-registro.md §3.1, invalidando a
#   identificacao dos degraus. Este orquestrador e camada ACIMA da escada e
#   nao pertence ao estado de codigo de nenhum degrau — mesmo argumento do
#   desvio declarado em 2026-09-02 (pre-registro.md §3.2).
#
# E PURAMENTE OBSERVACIONAL: nao altera configuracao, nao toca no fork, nao
# influencia o treino. Roda antes da serie e depois de cada execucao.
snapshot_ambiente() {
  local dest="$1"
  local pkgs="mesa-vulkan-drivers libgl1-mesa-dri mesa-libgallium libegl-mesa0"
  pkgs="$pkgs libglx-mesa0 libvulkan1 libdrm-amdgpu1 libdrm2"
  # libc6 e python3.12 acrescentados em 2026-09-21 depois de ler
  # /var/log/dpkg.log: ambos foram atualizados por unattended-upgrade em
  # 2026-09-21 06:36, ou seja ENTRE a ultima serie de D3 e a serie seguinte.
  # Importam porque libc6 carrega a libm, usada pelas metricas em PyTorch de
  # CPU, e porque o env.json do tcc_runner.py registra apenas a versao
  # upstream do Python ("3.12.3 (main, ...)"), que NAO distingue a revisao
  # Ubuntu 0.15 de 0.17.
  pkgs="$pkgs libc6 python3.12 libpython3.12t64"

  {
    printf '{\n'
    printf '  "snapshot_em": "%s",\n' "$(date -Is)"
    printf '  "kernel": "%s",\n'     "$(uname -r)"
    printf '  "uname_a": "%s",\n'    "$(uname -a | sed 's/"/\\"/g')"
    # boot_id distingue execucoes separadas por reinicio sem depender de
    # comparar timestamps a mao: foi um reinicio que ativou o kernel -31 entre
    # os dois blocos de D3, e nada nos dados de entao registrava isso.
    printf '  "boot_id": "%s",\n' \
      "$(cat /proc/sys/kernel/random/boot_id 2>/dev/null || echo 'INDISPONIVEL')"
    printf '  "pacotes": {\n'
    local first=1
    for p in $pkgs; do
      local v
      v="$(dpkg-query -W -f='${Version}' "$p" 2>/dev/null || true)"
      [ -n "$v" ] || v="AUSENTE"
      [ "$first" -eq 1 ] || printf ',\n'
      printf '    "%s": "%s"' "$p" "$v"
      first=0
    done
    printf '\n  },\n'
    # vulkaninfo veio VAZIO no inventario de 2026-08-25; por isso ha fallback
    # e por isso dpkg e a fonte primaria da versao, nao o vulkaninfo.
    printf '  "vulkan_driver": "%s",\n' \
      "$(vulkaninfo --summary 2>/dev/null \
         | grep -iE 'driverName|driverInfo|driverID' \
         | tr -s ' \t' ' ' | paste -sd'; ' - | sed 's/"/\\"/g' \
         || true)"
    printf '  "mesa_via_glxinfo": "%s"\n' \
      "$(glxinfo -B 2>/dev/null | grep -i 'OpenGL version' \
         | tr -s ' \t' ' ' | sed 's/"/\\"/g' || true)"
    printf '}\n'
  } > "$dest" 2>/dev/null

  # eco no terminal, para a heterogeneidade ficar visivel na hora e nao so
  # numa auditoria 11 dias depois
  printf '[ambiente] kernel=%s  mesa-vulkan-drivers=%s\n' \
    "$(uname -r)" \
    "$(dpkg-query -W -f='${Version}' mesa-vulkan-drivers 2>/dev/null || echo '?')"
}

snapshot_ambiente "$LOGS/ambiente-serie-$(date +%Y%m%dT%H%M%S).json"

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
git checkout --quiet "$TAG"
SHA="$(git rev-parse HEAD)"

echo "=========================================================="
echo " serie     : $DEGREE (tag $TAG)"
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
  if ! stdbuf -oL -eL python -u "$RUNNER" "$i" "$OUT_ROOT" "$DEGREE" --fork "$FORK/vksplat" 2>&1 | tee "$L"; then
    echo "ABORTA: execucao $IDX falhou (exit != 0). Ver $L" >&2
    exit 1
  fi

  # criterios de invalidacao — pre-registro §9.
  #
  # ATENCAO: o VkSplat COLORE a saida com codigos de escape ANSI. Diagnosticado
  # em 2026-09-08 via cat -A: a linha e, literalmente,
  #     Using device [^[[0m0^[[m]
  # ou seja, o indice vem embrulhado em ESC[0m ... ESC[m. Consequencias:
  #   - casar a string 'Using device [0]' NUNCA funciona;
  #   - extrair digitos sem limpar ANSI captura o '0' de '[0m' tambem, dando '00'.
  # Portanto: limpar ANSI PRIMEIRO, extrair depois.
  #
  # Principio geral: o log arquivado permanece bruto (e o registro primario);
  # a limpeza acontece na leitura, nunca na gravacao.

  DEV_LINE="$(grep -m1 'Using device' "$L" || true)"
  DEV_CLEAN="$(printf '%s' "$DEV_LINE" | sed -e 's/\x1B\[[0-9;]*[a-zA-Z]//g')"
  DEV_IDX="$(printf '%s' "$DEV_CLEAN" | tr -dc '0-9')"
  if [ "$DEV_IDX" != "0" ]; then
    echo "ABORTA: dispositivo inesperado (indice extraido='$DEV_IDX') em $L" >&2
    echo "        linha limpa : '$DEV_CLEAN'" >&2
    echo "        linha bruta, com bytes visiveis:" >&2
    printf '%s\n' "$DEV_LINE" | cat -A >&2
    exit 1
  fi

  grep -qF 'GFX1201' "$L" \
    || { echo "ABORTA: GPU esperada (GFX1201) nao enumerada em $L" >&2; exit 1; }

  ! grep -qiF 'USE_EMULATED' "$L" \
    || { echo "ABORTA: caminho emulado acionado em $L" >&2; exit 1; }

  # H3b: a perturbacao tem de ter sido aplicada e verificada nesta execucao
  python3 -c "import json,sys; e=json.load(open(sys.argv[1])); sys.exit(0 if (e.get('h3b') or {}).get('verificado') is True else 1)" \
      "$OUT_ROOT/$DEGREE/run$IDX/env.json" \
    || { echo "ABORTA: perturbacao de H3b nao verificada em run$IDX/env.json" >&2; exit 1; }

  # snapshot de ambiente por execucao, ao lado do env.json do tcc_runner.py.
  # Gravado DEPOIS do run porque o diretorio e criado pelo tcc_runner.py, e a
  # checagem de reutilizacao de indice acima exige que ele nao exista antes.
  RUN_DIR="$OUT_ROOT/$DEGREE/run$IDX"
  if [ -d "$RUN_DIR" ]; then
    snapshot_ambiente "$RUN_DIR/ambiente.json"
  else
    echo "AVISO: $RUN_DIR nao encontrado; ambiente.json nao gravado" >&2
  fi

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
