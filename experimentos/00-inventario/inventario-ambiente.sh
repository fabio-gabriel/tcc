#!/usr/bin/env bash
# =============================================================================
# Inventário de ambiente — Sprint 0, TCC Renderização Neural / Hardware Heterogêneo
#
# Objetivo: capturar o estado COMPLETO do ambiente antes de qualquer bring-up.
# A ausência de uma ferramenta é dado, não erro — o script nunca aborta por isso.
#
# Uso:
#   bash inventario-ambiente.sh                 # imprime e salva em ./saidas/
#   bash inventario-ambiente.sh /outro/destino  # salva em outro diretório
#
# Saída: markdown versionável, um arquivo por execução (hostname + data).
# =============================================================================

set -u  # nao usar 'set -e': queremos continuar mesmo com comandos ausentes

DESTINO="${1:-$(dirname "$0")/saidas}"
mkdir -p "$DESTINO"
STAMP="$(date -u +%Y%m%dT%H%M%SZ)"
ARQ="$DESTINO/inventario-$(hostname -s)-${STAMP}.md"

# --- helpers ----------------------------------------------------------------

# secao <titulo>
sec() { printf '\n## %s\n\n' "$1"; }

# sub <titulo>
sub() { printf '\n### %s\n\n' "$1"; }

# run <rotulo> <comando...>  — executa e emite em bloco de código
run() {
  local rotulo="$1"; shift
  printf '**%s** — `%s`\n\n' "$rotulo" "$*"
  printf '```\n'
  if command -v "$1" >/dev/null 2>&1 || [ -e "$1" ]; then
    "$@" 2>&1 | sed 's/\r$//'
    local rc=${PIPESTATUS[0]}
    [ "$rc" -ne 0 ] && printf '\n[exit code: %s]\n' "$rc"
  else
    printf '[AUSENTE: comando "%s" não encontrado no PATH]\n' "$1"
  fi
  printf '```\n\n'
}

# runsh <rotulo> <string de shell>  — para pipes/globs
runsh() {
  local rotulo="$1"; shift
  printf '**%s** — `%s`\n\n' "$rotulo" "$*"
  printf '```\n'
  eval "$*" 2>&1 | sed 's/\r$//'
  printf '```\n\n'
}

# =============================================================================
# Início da captura
# =============================================================================
{
printf '# Inventário de ambiente — %s\n\n' "$(hostname -s)"
printf -- '- **Data/hora (UTC):** %s\n' "$(date -u +%Y-%m-%dT%H:%M:%SZ)"
printf -- '- **Data/hora (local):** %s\n' "$(date +%Y-%m-%dT%H:%M:%S%z)"
printf -- '- **Usuário:** %s\n' "$(id -un)"
printf -- '- **Script:** `%s`\n' "$0"
printf -- '- **Propósito:** Sprint 0, item "caderno de campo" — estado do ambiente antes do bring-up.\n'

# -----------------------------------------------------------------------------
sec 'Sistema operacional e kernel'
# ROCm 7.x exige point-release exata (Ubuntu 24.04.4 / 22.04.5 conforme doc AMD).
# Divergência aqui já é achado do TCC.
run 'Kernel'            uname -a
runsh 'Distribuição'    'cat /etc/os-release'
run 'lsb_release'       lsb_release -a
runsh 'Point release'   'cat /etc/lsb-release 2>/dev/null; cat /var/log/installer/media-info 2>/dev/null'
run 'Uptime'            uptime

# -----------------------------------------------------------------------------
sec 'CPU, memória e disco'
# Registrado para (a) comparabilidade futura contra o host da vast.ai,
# (b) NeRF/3DGS têm componente real de CPU/IO no dataloading.
runsh 'CPU'             'lscpu | head -30'
runsh 'Memória'         'free -h; echo; grep -E "MemTotal|SwapTotal" /proc/meminfo'
runsh 'Disco'           'df -h / /home "$HOME" 2>/dev/null | sort -u'
runsh 'Espaço livre em $HOME' 'du -sh "$HOME" 2>/dev/null | tail -1; df -h "$HOME" | tail -1'

# -----------------------------------------------------------------------------
sec 'GPU: hardware e driver de kernel'
runsh 'PCI (VGA/Display)' 'lspci -nn | grep -Ei "vga|display|3d"'
runsh 'PCI detalhado (link width/speed)' 'lspci -vv 2>/dev/null | grep -A3 -Ei "vga|display" | grep -Ei "vga|display|lnksta|lnkcap" || echo "[requer root para LnkSta]"'
run  'Módulo amdgpu carregado' lsmod
runsh 'amdgpu (filtrado)' 'lsmod | grep -E "^amdgpu|^amdkfd|^amdttm" || echo "[amdgpu NAO carregado]"'
runsh 'Versão do módulo amdgpu' 'modinfo amdgpu 2>/dev/null | grep -E "^(filename|version|srcversion|vermagic):" || echo "[modinfo amdgpu falhou]"'
runsh 'DKMS (amdgpu-pro instalado?)' 'dkms status 2>/dev/null || echo "[dkms ausente — provavelmente amdgpu in-kernel]"'
runsh 'dmesg amdgpu' 'dmesg 2>/dev/null | grep -i amdgpu | tail -40 || journalctl -k 2>/dev/null | grep -i amdgpu | tail -40 || echo "[sem acesso a dmesg/journalctl sem root]"'
runsh 'Firmware carregado' 'dmesg 2>/dev/null | grep -iE "amdgpu.*(firmware|fw|vbios|ip block)" | tail -30 || echo "[indisponivel]"'

# -----------------------------------------------------------------------------
sec 'Permissões de acesso à GPU'
# ROCm requer o usuário nos grupos 'render' e 'video'. Falha aqui explica
# 90% dos "rocminfo: no permission" e é erro de setup, não de suporte.
run  'Grupos do usuário' id
runsh 'Grupos render/video' 'id -nG | tr " " "\n" | grep -E "^(render|video)$" || echo "[AVISO: usuário NAO esta em render e/ou video — ROCm vai falhar]"'
runsh 'Nós de dispositivo' 'ls -l /dev/kfd /dev/dri/ 2>&1'

# -----------------------------------------------------------------------------
sec 'ROCm: instalação e versão'
runsh 'ROCm presente?'  'ls -d /opt/rocm* 2>/dev/null || echo "[/opt/rocm NAO existe — ROCm nao instalado]"'
runsh 'Versão ROCm'     'cat /opt/rocm/.info/version 2>/dev/null; cat /opt/rocm/.info/version-dev 2>/dev/null; echo "---"; ls /opt/rocm/.info/ 2>/dev/null'
run  'hipconfig'        hipconfig --version
runsh 'hipconfig full'  'hipconfig 2>&1 | head -40'
run  'rocm-smi versão'  rocm-smi --version
runsh 'Pacotes ROCm (dpkg)' 'dpkg -l 2>/dev/null | grep -iE "rocm|hip|miopen|rocblas|rccl|rocwmma|hsa" | awk "{print \$2, \$3}" || echo "[dpkg indisponivel]"'
runsh 'Repositório APT AMD' 'grep -rIh "repo.radeon.com" /etc/apt/sources.list /etc/apt/sources.list.d/ 2>/dev/null || echo "[nenhum repo AMD em sources.list]"'

# -----------------------------------------------------------------------------
sec 'ROCm: a GPU é enxergada como gfx1201?'
# Esperado para RX 9070 XT (RDNA 4): gfx1201.
runsh 'rocminfo (agentes)' 'rocminfo 2>&1 | grep -E "Name:|Marketing Name:|gfx|Compute Unit|Wavefront|Device Type" | head -40 || echo "[rocminfo falhou ou ausente]"'
runsh 'Alvo gfx detectado' 'rocminfo 2>/dev/null | grep -oE "gfx[0-9a-f]+" | sort -u || echo "[nenhum alvo gfx detectado]"'
run  'rocm-smi (visão geral)' rocm-smi
runsh 'rocm-smi --showhw' 'rocm-smi --showhw 2>&1'
runsh 'clinfo (OpenCL)'  'clinfo 2>&1 | grep -E "Device Name|Device Version|Driver Version|Max compute units" | head -20 || echo "[clinfo ausente]"'

# -----------------------------------------------------------------------------
sec 'ROCm: instrumentação de potência (gate da hipótese H3)'
# Duas perguntas: (1) o sensor responde? (2) o valor é plausível e variável,
# ou constante/zero/N/A (sensor morto)? Amostragem em idle estabelece o piso.
runsh 'showpower'        'rocm-smi --showpower 2>&1'
runsh 'showpower --json' 'rocm-smi --showpower --json 2>&1'
runsh 'showtemp'         'rocm-smi --showtemp 2>&1'
runsh 'showpower+temp+clocks (--showallinfo é verboso; recorte)' 'rocm-smi --showpower --showtemp --showclocks 2>&1'
sub 'Amostragem em idle (10 leituras, ~1 s de intervalo)'
printf 'Se as 10 leituras forem idênticas e "redondas" (ex.: sempre 0.0W), suspeitar de sensor não implementado.\n\n'
printf '```\n'
if command -v rocm-smi >/dev/null 2>&1; then
  for i in $(seq 1 10); do
    printf 'amostra %02d @ %s : ' "$i" "$(date +%H:%M:%S.%3N 2>/dev/null || date +%H:%M:%S)"
    rocm-smi --showpower 2>&1 | grep -iE "power|W" | tr -s ' ' | paste -sd' | ' -
    sleep 1
  done
else
  printf '[AUSENTE: rocm-smi]\n'
fi
printf '```\n\n'
runsh 'Sensores via sysfs (fallback se rocm-smi falhar)' 'for f in /sys/class/drm/card*/device/hwmon/hwmon*/power*_average /sys/class/drm/card*/device/hwmon/hwmon*/power*_input; do [ -e "$f" ] && echo "$f = $(cat "$f" 2>/dev/null)"; done || echo "[sem power em hwmon]"'
runsh 'hwmon disponível'  'ls /sys/class/drm/card*/device/hwmon/hwmon*/ 2>/dev/null | sort -u | head -40 || echo "[sem hwmon]"'

# -----------------------------------------------------------------------------
sec 'Vulkan (rota do VkSplat — independente do ROCm)'
# VkSplat não usa ROCm. Esta seção pode passar mesmo se ROCm estiver quebrado.
run  'vulkaninfo --summary' vulkaninfo --summary
runsh 'Driver Vulkan (RADV vs AMDVLK)' 'vulkaninfo 2>/dev/null | grep -iE "driverName|driverInfo|driverID|deviceName|apiVersion" | sort -u | head -20 || echo "[vulkaninfo falhou]"'
runsh 'ICDs Vulkan instalados' 'ls -1 /usr/share/vulkan/icd.d/ /etc/vulkan/icd.d/ 2>/dev/null || echo "[sem ICDs]"'
runsh 'Pacotes Vulkan/Mesa' 'dpkg -l 2>/dev/null | grep -iE "vulkan|mesa|libdrm|radv|amdvlk" | awk "{print \$2, \$3}" || echo "[dpkg indisponivel]"'
sub 'Extensões relevantes para matmul em Vulkan'
printf 'VK_KHR_cooperative_matrix é a exposição, em Vulkan, das unidades matriciais (WMMA em RDNA).\n'
printf 'Presença/ausência aqui é dado direto para a discussão Tensor Core vs WMMA (Cap. 3/5).\n\n'
runsh 'cooperative_matrix / subgroup / FP16' 'vulkaninfo 2>/dev/null | grep -iE "cooperative_matrix|VK_KHR_shader_float16|subgroupSize|shaderFloat16|VK_KHR_16bit_storage|VK_EXT_subgroup" | sort -u | head -30 || echo "[vulkaninfo falhou]"'
runsh 'Filas de compute' 'vulkaninfo 2>/dev/null | grep -iE "queueFlags|queueCount" | head -20 || echo "[indisponivel]"'
runsh 'Compilador de shaders' 'for c in glslc glslangValidator spirv-val shaderc; do printf "%s: " "$c"; command -v "$c" >/dev/null 2>&1 && "$c" --version 2>&1 | head -1 || echo "[ausente]"; done'

# -----------------------------------------------------------------------------
sec 'Python, PyTorch e Taichi'
runsh 'Pythons disponíveis' 'for p in python3 python3.10 python3.11 python3.12 python3.13; do printf "%s: " "$p"; command -v "$p" >/dev/null 2>&1 && "$p" --version 2>&1 || echo "[ausente]"; done'
run  'pip'              python3 -m pip --version
runsh 'venv/conda ativo?' 'echo "VIRTUAL_ENV=${VIRTUAL_ENV:-<nenhum>}"; echo "CONDA_PREFIX=${CONDA_PREFIX:-<nenhum>}"; command -v conda >/dev/null 2>&1 && conda --version || echo "conda: [ausente]"'
sub 'PyTorch — build e visibilidade da GPU'
printf '```\n'
if command -v python3 >/dev/null 2>&1; then
python3 - <<'PY' 2>&1
try:
    import torch
    print("torch.__version__      :", torch.__version__)
    print("torch.version.hip      :", getattr(torch.version, "hip", None))
    print("torch.version.cuda     :", getattr(torch.version, "cuda", None))
    print("is_available()         :", torch.cuda.is_available())
    print("device_count()         :", torch.cuda.device_count())
    for i in range(torch.cuda.device_count()):
        print(f"  [{i}] name          :", torch.cuda.get_device_name(i))
        print(f"  [{i}] capability    :", torch.cuda.get_device_capability(i))
        p = torch.cuda.get_device_properties(i)
        print(f"  [{i}] gcnArchName   :", getattr(p, "gcnArchName", "n/a"))
        print(f"  [{i}] total_memory  :", round(p.total_memory / 1024**3, 2), "GiB")
    print("bf16 suportado         :", torch.cuda.is_bf16_supported() if torch.cuda.is_available() else "n/a")
except ImportError as e:
    print("[AUSENTE] PyTorch nao importavel:", e)
except Exception as e:
    print("[ERRO] PyTorch importou mas falhou:", type(e).__name__, e)
PY
else
  printf '[AUSENTE: python3]\n'
fi
printf '```\n\n'
sub 'Taichi — backends detectados'
printf '```\n'
if command -v python3 >/dev/null 2>&1; then
python3 - <<'PY' 2>&1
try:
    import taichi as ti
    print("taichi.__version__:", ti.__version__)
    for backend_name in ("vulkan", "cpu", "opengl", "amdgpu", "cuda"):
        arch = getattr(ti, backend_name, None)
        if arch is None:
            print(f"  {backend_name:8s}: [arch inexistente nesta versao]")
            continue
        try:
            ti.init(arch=arch, log_level=ti.ERROR)
            print(f"  {backend_name:8s}: OK -> arch efetiva = {ti.lang.impl.current_cfg().arch}")
        except Exception as e:
            print(f"  {backend_name:8s}: FALHOU -> {type(e).__name__}: {str(e)[:120]}")
except ImportError as e:
    print("[AUSENTE] Taichi nao importavel:", e)
except Exception as e:
    print("[ERRO]", type(e).__name__, e)
PY
else
  printf '[AUSENTE: python3]\n'
fi
printf '```\n\n'
runsh 'Pacotes Python relevantes' 'python3 -m pip list 2>/dev/null | grep -iE "torch|taichi|nerfstudio|gsplat|numpy|opencv|plyfile|tinycudann|colmap|lpips|scikit-image" || echo "[pip list falhou ou nada relevante]"'

# -----------------------------------------------------------------------------
sec 'Toolchain de build'
runsh 'Compiladores' 'for c in gcc g++ clang clang++ hipcc amdclang++; do printf "%s: " "$c"; command -v "$c" >/dev/null 2>&1 && "$c" --version 2>&1 | head -1 || echo "[ausente]"; done'
runsh 'Build tools' 'for c in cmake ninja make git pkg-config; do printf "%s: " "$c"; command -v "$c" >/dev/null 2>&1 && "$c" --version 2>&1 | head -1 || echo "[ausente]"; done'
runsh 'COLMAP (SfM para datasets próprios)' 'command -v colmap >/dev/null 2>&1 && colmap --help 2>&1 | head -3 || echo "[ausente — necessario apenas para cenas proprias]"'
runsh 'ffmpeg' 'command -v ffmpeg >/dev/null 2>&1 && ffmpeg -version 2>&1 | head -1 || echo "[ausente]"'

# -----------------------------------------------------------------------------
sec 'Rede e contexto'
runsh 'Hostname / IPs' 'hostname -f 2>/dev/null; ip -brief addr 2>/dev/null | grep -v "^lo" || ifconfig 2>/dev/null | head -20'
runsh 'Tailscale' 'command -v tailscale >/dev/null 2>&1 && tailscale status 2>&1 | head -10 || echo "[tailscale ausente]"'
runsh 'Docker (opcional, p/ fixar ambiente)' 'command -v docker >/dev/null 2>&1 && docker --version && docker info 2>/dev/null | grep -iE "server version|storage driver" || echo "[docker ausente]"'

# -----------------------------------------------------------------------------
sec 'Resumo automático (checklist de gates do Sprint 0)'
printf '| Gate | Resultado |\n|---|---|\n'
chk() { printf '| %s | %s |\n' "$1" "$2"; }

if rocminfo 2>/dev/null | grep -q gfx1201; then
  chk 'ROCm enxerga gfx1201 (RDNA 4)' 'SIM'
elif rocminfo 2>/dev/null | grep -qoE 'gfx[0-9a-f]+'; then
  chk 'ROCm enxerga gfx1201 (RDNA 4)' "NAO — detectado: $(rocminfo 2>/dev/null | grep -oE 'gfx[0-9a-f]+' | sort -u | paste -sd, -)"
else
  chk 'ROCm enxerga gfx1201 (RDNA 4)' 'NAO — rocminfo falhou/ausente'
fi

if command -v rocm-smi >/dev/null 2>&1 && rocm-smi --showpower 2>/dev/null | grep -qiE '[0-9]+\.[0-9]+'; then
  chk 'rocm-smi reporta potência numérica (gate H3)' 'SIM — validar variação sob carga no passo 2'
else
  chk 'rocm-smi reporta potência numérica (gate H3)' 'NAO / indeterminado — acionar plano B (wattímetro)'
fi

if python3 -c 'import torch,sys; sys.exit(0 if torch.cuda.is_available() else 1)' 2>/dev/null; then
  chk 'PyTorch vê a GPU (gate 3DGS-HIP + baseline)' 'SIM'
else
  chk 'PyTorch vê a GPU (gate 3DGS-HIP + baseline)' 'NAO'
fi

if vulkaninfo --summary >/dev/null 2>&1; then
  chk 'Vulkan operacional (gate VkSplat — desenho 2x2)' 'SIM'
else
  chk 'Vulkan operacional (gate VkSplat — desenho 2x2)' 'NAO'
fi

if vulkaninfo 2>/dev/null | grep -qi cooperative_matrix; then
  chk 'VK_KHR_cooperative_matrix (WMMA via Vulkan)' 'SIM'
else
  chk 'VK_KHR_cooperative_matrix (WMMA via Vulkan)' 'NAO / nao detectado'
fi

if id -nG 2>/dev/null | tr ' ' '\n' | grep -qx render && id -nG 2>/dev/null | tr ' ' '\n' | grep -qx video; then
  chk 'Usuário em render+video' 'SIM'
else
  chk 'Usuário em render+video' 'NAO — corrigir antes de qualquer teste ROCm'
fi

printf '\n---\n\n'
printf '_Gerado por `inventario-ambiente.sh` em %s._\n' "$(date -u +%Y-%m-%dT%H:%M:%SZ)"

} 2>&1 | tee "$ARQ"

printf '\n\n>>> Inventário salvo em: %s\n' "$ARQ"
