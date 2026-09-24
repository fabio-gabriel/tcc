#!/usr/bin/env bash
# Teste do risco tecnico nao mitigado de D4 — pre-registro.md §10.6.
#
# PERGUNTA A RESPONDER
#   O `slangc` emite SPIR-V valido para `InterlockedAdd` INTEIRO sobre
#   `RWByteAddressBuffer`?
#
# Por que importa: nao existe, em nenhum `.slang` do repositorio do VkSplat nem
# em nenhum `.spv` versionado, precedente dessa chamada. D4 estreia essa API. Se
# o slangc nao a suportar, D4 exige outro desenho — e e melhor descobrir agora,
# em minutos, do que depois de implementar quatro arquivos de shader.
#
# O teste tambem responde duas perguntas secundarias:
#   - qual assinatura de InterlockedAdd o Slang aceita (2 ou 3 argumentos,
#     uint ou int), porque isso determina como o `_ATOMIC_ADD_FIXED` do §10.2
#     tem de ser escrito;
#   - se o SPIR-V gerado contem `OpAtomicIAdd`, que e a instrucao cuja
#     semantica de wraparound o desenho de D4 depende.
#
# NAO INSTALA NADA NO SISTEMA. A toolchain fica sob --prefix (padrao ~/opt), e
# nada e escrito fora de lá e do diretorio de saida. Isso preserva o ambiente
# congelado em 2026-09-21.
#
# ATENCAO, ARMADILHA DOCUMENTADA: nao instale `slang` pelo apt. O pacote apt com
# esse nome e a S-Lang, biblioteca de terminal sem nenhuma relacao — conflito
# atestado pelo proprio docs/building.md do Slang.
#
# Uso:
#   bash testar_slang_atomic.sh                    # usa ~/opt, baixa se preciso
#   bash testar_slang_atomic.sh --prefix /caminho  # outro prefixo
#   bash testar_slang_atomic.sh --slangc /caminho/slangc   # binario ja existente

set -euo pipefail

VERSAO="2026.2.1"                       # pinada: a versao com que o VkSplat foi
                                        # testado. A release corrente e ~30
                                        # versoes a frente e a ABI nao e estavel.
ASSET="slang-${VERSAO}-linux-x86_64.tar.gz"
URL="https://github.com/shader-slang/slang/releases/download/v${VERSAO}/${ASSET}"
BYTES_ESPERADOS=70742686                # verificado em 2026-09-21

PREFIX="$HOME/opt"
SLANGC=""
OUT="$HOME/tcc-runs/slang-teste"

while [ $# -gt 0 ]; do
  case "$1" in
    --prefix) PREFIX="$2"; shift 2 ;;
    --slangc) SLANGC="$2"; shift 2 ;;
    --out)    OUT="$2"; shift 2 ;;
    *) echo "argumento desconhecido: $1" >&2; exit 64 ;;
  esac
done

mkdir -p "$OUT"
REL="$OUT/relatorio.txt"
: > "$REL"
log() { printf '%s\n' "$*" | tee -a "$REL"; }

log "=== Teste §10.6 — InterlockedAdd inteiro sobre RWByteAddressBuffer ==="
log "data: $(date -Is)"
log "host: $(hostname)  kernel: $(uname -r)"
log ""

# ---------------------------------------------------------------------------
# 1. toolchain
# ---------------------------------------------------------------------------
if [ -z "$SLANGC" ]; then
  DEST="$PREFIX/slang-$VERSAO"
  SLANGC="$DEST/bin/slangc"
  if [ ! -x "$SLANGC" ]; then
    mkdir -p "$PREFIX"
    TAR="$PREFIX/$ASSET"
    if [ ! -f "$TAR" ]; then
      # Se o asset ja foi baixado a mao, procura nos lugares habituais antes de
      # gastar rede de novo.
      for cand in "$HOME/Downloads/$ASSET" "$HOME/$ASSET" "./$ASSET"; do
        if [ -f "$cand" ]; then
          log "asset encontrado em $cand"
          cp "$cand" "$TAR"
          break
        fi
      done
    fi
    if [ ! -f "$TAR" ]; then
      log "baixando $ASSET"
      curl -fL --proto '=https' --tlsv1.2 -o "$TAR" "$URL"
    fi

    # Verificacao de integridade. O tamanho foi verificado em fonte primaria em
    # 2026-09-21; o SHA-256 e registrado aqui porque e pendencia aberta do
    # caderno de campo ("Registrar o SHA-256 do asset da Slang").
    TAM="$(stat -c%s "$TAR")"
    SHA="$(sha256sum "$TAR" | cut -d' ' -f1)"
    log "asset   : $ASSET"
    log "bytes   : $TAM (esperado $BYTES_ESPERADOS)"
    log "sha256  : $SHA"
    if [ "$TAM" != "$BYTES_ESPERADOS" ]; then
      log "ABORTA: tamanho divergente. Nao prosseguir com asset nao conferido."
      exit 1
    fi
    log "tamanho confere."
    mkdir -p "$DEST"

    # Detecta a estrutura do tar em vez de assumir. Alguns releases empacotam
    # tudo sob um diretorio raiz (`slang-X/bin/...`), outros poem `bin/` na
    # propria raiz. `--strip-components=1` fixo destruiria o segundo caso,
    # removendo o proprio `bin`. Verificar custa uma listagem.
    PRIMEIRO_NIVEL="$(tar -tzf "$TAR" | sed 's#/.*##' | sort -u)"
    if printf '%s\n' "$PRIMEIRO_NIVEL" | grep -qx "bin"; then
      log "estrutura do tar: bin/ na raiz -> extraindo sem strip"
      tar -xzf "$TAR" -C "$DEST"
    elif [ "$(printf '%s\n' "$PRIMEIRO_NIVEL" | wc -l)" -eq 1 ]; then
      log "estrutura do tar: diretorio raiz unico ($PRIMEIRO_NIVEL) -> strip 1"
      tar -xzf "$TAR" -C "$DEST" --strip-components=1
    else
      log "estrutura do tar inesperada, primeiro nivel:"
      printf '%s\n' "$PRIMEIRO_NIVEL" | sed 's/^/    /' | tee -a "$REL"
      log "ABORTA: extraia manualmente e use --slangc para apontar o binario."
      exit 1
    fi
  fi
fi

if [ ! -x "$SLANGC" ]; then
  log "ABORTA: slangc nao encontrado/executavel em $SLANGC"
  log "        Se extraiu a mao, aponte com: --slangc /caminho/bin/slangc"
  exit 1
fi

log ""
log "slangc  : $SLANGC"
log "versao  : $("$SLANGC" -v 2>&1 | head -2 | tr '\n' ' ')"
log ""

# --- armadilha de biblioteca dinamica, documentada pelo proprio Slang --------
# O "Getting Started" oficial avisa: no Linux, LD_LIBRARY_PATH SOBREPOE o RUNPATH
# embutido no slangc, e com mais de uma Slang instalada (por exemplo a que vem no
# Vulkan SDK) o binario pode carregar `libslang-compiler.so` da versao errada,
# levando a "version mismatches and unexpected behavior".
#
# Num trabalho cujo objeto e reprodutibilidade numerica, compilar shaders com uma
# versao de compilador diferente da declarada seria exatamente o tipo de erro
# silencioso que este projeto ja pagou caro. Por isso se registra de ONDE cada
# biblioteca esta sendo carregada, em vez de confiar no caminho do executavel.
log "--- bibliotecas dinamicas efetivamente carregadas ---"
if [ -n "${LD_LIBRARY_PATH:-}" ]; then
  log "ATENCAO: LD_LIBRARY_PATH esta definido e sobrepoe o RUNPATH do slangc:"
  log "         $LD_LIBRARY_PATH"
  log "         Se alguma libslang vier de fora de $(dirname "$SLANGC")/../lib,"
  log "         a versao compilando os shaders NAO e a declarada. Considere"
  log "         rodar com: env -u LD_LIBRARY_PATH bash $0 ..."
else
  log "LD_LIBRARY_PATH nao definido (bom: vale o RUNPATH embutido)"
fi
if command -v ldd >/dev/null 2>&1; then
  ldd "$SLANGC" 2>/dev/null | grep -i "slang\|glslang" | sed 's/^/  /' \
    | tee -a "$REL" || log "  (nenhuma libslang listada por ldd)"
else
  log "  ldd ausente; procedencia das bibliotecas nao verificada"
fi
log ""

# spirv-dis e opcional: se ausente, cai para busca binaria pela instrucao.
DIS="$(command -v spirv-dis || true)"
log "spirv-dis: ${DIS:-ausente (sera usada inspecao alternativa)}"
log ""

# ---------------------------------------------------------------------------
# 2. variantes. Compiladas SEPARADAMENTE de proposito: se uma nao compila, as
#    outras ainda sao testadas. Um arquivo unico daria um unico veredito e
#    esconderia qual assinatura o Slang aceita.
# ---------------------------------------------------------------------------
SRC="$OUT/src"; mkdir -p "$SRC"

cat > "$SRC/v1_uint_2args.slang" <<'SLANG'
// Assinatura de 2 argumentos, valor uint. E a forma mais proxima do que o
// §10.2 pretende escrever como macro _ATOMIC_ADD_FIXED.
RWByteAddressBuffer accum;
[numthreads(64, 1, 1)]
void main(uint3 tid : SV_DispatchThreadID) {
    accum.InterlockedAdd(tid.x * 4, 1u);
}
SLANG

cat > "$SRC/v2_uint_3args.slang" <<'SLANG'
// Assinatura de 3 argumentos, com valor original de saida (forma canonica em
// HLSL). Se so esta compilar, a macro precisa de uma variavel descartavel.
RWByteAddressBuffer accum;
[numthreads(64, 1, 1)]
void main(uint3 tid : SV_DispatchThreadID) {
    uint original;
    accum.InterlockedAdd(tid.x * 4, 1u, original);
}
SLANG

cat > "$SRC/v3_int_negativo.slang" <<'SLANG'
// O caso que D4 realmente precisa: valores COM SINAL, positivos e negativos,
// porque gradientes tem os dois sinais. Se apenas uint for aceito, o valor
// negativo entra por reinterpretacao de bits (asuint), e a soma em dois
// complementos continua correta modulo 2^32.
RWByteAddressBuffer accum;
[numthreads(64, 1, 1)]
void main(uint3 tid : SV_DispatchThreadID) {
    int v = int(tid.x) - 32;           // -32 .. +31
    accum.InterlockedAdd(tid.x * 4, asuint(v));
}
SLANG

cat > "$SRC/v4_int_direto.slang" <<'SLANG'
// Passando int sem conversao explicita, para descobrir se ha sobrecarga int.
RWByteAddressBuffer accum;
[numthreads(64, 1, 1)]
void main(uint3 tid : SV_DispatchThreadID) {
    int v = int(tid.x) - 32;
    accum.InterlockedAdd(tid.x * 4, v);
}
SLANG

cat > "$SRC/v5_nove_sitios.slang" <<'SLANG'
// Ensaio do formato real de D4: nove acumuladores sobre tres buffers, com
// escalas por componente como as medidas em 2026-09-23. Verifica que o padrao
// completo compila, nao apenas uma chamada isolada.
RWByteAddressBuffer v_xy_vs;
RWByteAddressBuffer v_inv_cov_vs_opacity;
RWByteAddressBuffer v_rgb;

static const float ESCALA_XY      = 17592186044416.0;  // 2^44
static const float ESCALA_CONIC01 = 262144.0;          // 2^18
static const float ESCALA_CONIC2  = 1048576.0;         // 2^20
static const float ESCALA_OPAC    = 17179869184.0;     // 2^34
static const float ESCALA_RGB     = 137438953472.0;    // 2^37

// Arredondamento ao mais proximo, NAO truncamento: truncamento introduz vies
// sistematico, que nao cancela na media acumulada usada pelo teste de limiar da
// densificacao em computeGrowMask.
int paraFixo(float x, float escala) { return int(round(x * escala)); }

[numthreads(64, 1, 1)]
void main(uint3 tid : SV_DispatchThreadID) {
    uint i = tid.x;
    float g = float(i) * 1e-6;

    v_xy_vs.InterlockedAdd((i * 2 + 0) * 4, asuint(paraFixo(g, ESCALA_XY)));
    v_xy_vs.InterlockedAdd((i * 2 + 1) * 4, asuint(paraFixo(-g, ESCALA_XY)));

    v_inv_cov_vs_opacity.InterlockedAdd((i * 4 + 0) * 4, asuint(paraFixo(g, ESCALA_CONIC01)));
    v_inv_cov_vs_opacity.InterlockedAdd((i * 4 + 1) * 4, asuint(paraFixo(g, ESCALA_CONIC01)));
    v_inv_cov_vs_opacity.InterlockedAdd((i * 4 + 2) * 4, asuint(paraFixo(g, ESCALA_CONIC2)));
    v_inv_cov_vs_opacity.InterlockedAdd((i * 4 + 3) * 4, asuint(paraFixo(g, ESCALA_OPAC)));

    v_rgb.InterlockedAdd((i * 3 + 0) * 4, asuint(paraFixo(g, ESCALA_RGB)));
    v_rgb.InterlockedAdd((i * 3 + 1) * 4, asuint(paraFixo(g, ESCALA_RGB)));
    v_rgb.InterlockedAdd((i * 3 + 2) * 4, asuint(paraFixo(g, ESCALA_RGB)));
}
SLANG

cat > "$SRC/v6_float_atomic.slang" <<'SLANG'
// Controle. Este e o mecanismo ATUAL do VkSplat (atomico de ponto flutuante).
// Serve para distinguir "o slangc nao suporta atomico nenhum neste contexto" de
// "o slangc nao suporta o atomico INTEIRO". Sem este controle, uma falha geral
// seria lida como falha especifica de D4.
RWByteAddressBuffer accum;
[numthreads(64, 1, 1)]
void main(uint3 tid : SV_DispatchThreadID) {
    accum.InterlockedAddF32(tid.x * 4, 1.0f);
}
SLANG

# ---------------------------------------------------------------------------
# 3. compilar e inspecionar
# ---------------------------------------------------------------------------
log "--- compilacao ---"
OK=0; FALHOU=0
declare -a APROVADAS=()

for f in "$SRC"/*.slang; do
  nome="$(basename "$f" .slang)"
  spv="$OUT/$nome.spv"
  err="$OUT/$nome.stderr.txt"
  # -fp-mode precise: nao autorizar transformacoes de ponto flutuante durante um
  # teste cujo objeto e comportamento numerico. Nota: a documentacao do Slang
  # NAO afirma que `fast` autoriza reassociacao — ver correcao de 2026-09-21.
  # -denorm-mode-fp32 preserve: o compile_shaders.py do VkSplat NAO fixa esta
  # opcao, cujo default e "implementation defined" (§10.8). Fixada aqui.
  if "$SLANGC" "$f" \
        -target spirv -stage compute -entry main \
        -fp-mode precise \
        -denorm-mode-fp32 preserve \
        -o "$spv" 2> "$err"; then
    bytes="$(stat -c%s "$spv" 2>/dev/null || echo 0)"
    log "  OK      $nome  (${bytes} bytes)"
    APROVADAS+=("$nome")
    OK=$((OK+1))
  else
    log "  FALHOU  $nome"
    sed 's/^/            /' "$err" | head -6 | tee -a "$REL" >/dev/null
    head -6 "$err" | sed 's/^/            /'
    FALHOU=$((FALHOU+1))
  fi
done

log ""
log "--- instrucoes atomicas no SPIR-V gerado ---"
for nome in "${APROVADAS[@]:-}"; do
  [ -n "$nome" ] || continue
  spv="$OUT/$nome.spv"
  if [ -n "$DIS" ]; then
    asm="$OUT/$nome.spvasm"
    "$DIS" "$spv" > "$asm" 2>/dev/null || true
    iadd=$(grep -c "OpAtomicIAdd" "$asm" 2>/dev/null || true)
    fadd=$(grep -c "OpAtomicFAddEXT" "$asm" 2>/dev/null || true)
    caps=$(grep -oE "OpCapability [A-Za-z0-9]+" "$asm" 2>/dev/null | sort -u | tr '\n' ' ')
    log "  $nome: OpAtomicIAdd=${iadd:-0}  OpAtomicFAddEXT=${fadd:-0}"
    log "      capabilities: $caps"
  else
    # Sem spirv-dis: `strings` nao serve para SPIR-V binario, mas o opcode de
    # OpAtomicIAdd (234) nao e localizavel de forma confiavel sem desmontar.
    # Portanto o veredito de compilacao vale; o de instrucao fica pendente.
    log "  $nome: compilou, mas instrucao nao verificada (spirv-dis ausente)"
  fi
done

log ""
log "--- veredito ---"
log "compilaram: $OK   falharam: $FALHOU"

_tem() { printf '%s\n' "${APROVADAS[@]:-}" | grep -qx "$1"; }

if _tem v5_nove_sitios; then
  log "DESTRAVADO: o padrao completo de D4 (9 sitios, 3 buffers, escalas por"
  log "            componente) compila para SPIR-V. O risco do §10.6 esta"
  log "            mitigado para o proposito de compilacao."
elif _tem v1_uint_2args || _tem v2_uint_3args || _tem v3_int_negativo || _tem v4_int_direto; then
  log "PARCIAL: InterlockedAdd inteiro compila em forma isolada, mas o ensaio"
  log "         dos 9 sitios nao. Investigar a mensagem de erro de v5 antes de"
  log "         concluir qualquer coisa sobre viabilidade."
else
  log "BLOQUEADO: nenhuma variante de InterlockedAdd inteiro compilou."
  if _tem v6_float_atomic; then
    log "           O controle de ponto flutuante (v6) COMPILOU, portanto a"
    log "           limitacao e especifica do atomico inteiro. D4 exige outro"
    log "           desenho — ver §10.6."
  else
    log "           O controle de ponto flutuante (v6) TAMBEM falhou, portanto o"
    log "           problema provavelmente e de invocacao do slangc e NAO da"
    log "           API. Corrigir a invocacao antes de concluir sobre D4."
  fi
fi

log ""
log "O QUE ESTE TESTE NAO RESPONDE:"
log "  - se OpAtomicIAdd faz wraparound (e nao saturacao) em estouro. E disso"
log "    que a bit-identidade de D4 depende, porque soma modular e associativa"
log "    e saturacao nao e. Exige leitura da especificacao SPIR-V da Khronos."
log "  - se o RADV executa a instrucao corretamente em gfx1201. Compilar nao e"
log "    executar."
log ""
log "relatorio: $REL"
log "artefatos: $OUT"
