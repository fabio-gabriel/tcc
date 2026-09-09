# Caderno de campo — bring-up

> Registro cronológico das tentativas de instalação e configuração do ambiente experimental.
>
> **Por que este arquivo existe (justificativa corrigida em 2026-09-02).** Três funções, todas no escopo atual do TCC:
>
> 1. **Proveniência do ambiente para o Cap. 4.** Versões de SO, kernel, driver, Mesa, Python e dependências; commit fixado do VkSplat; quais patches foram aplicados e em que ordem; qual GLM foi usado. Sem esse registro o experimento não é reprodutível por terceiros — o que seria autocontraditório num trabalho sobre reprodutibilidade.
> 2. **N0 como resultado.** O bring-up em RDNA 4 é o primeiro nível de evidência do `PLANO.md` §2.4, porque os autores do VkSplat nunca testaram essa arquitetura. Uma falha documentada também é dado.
> 3. **Registro de decisões e de erros.** A disciplina de método do projeto, que já impediu dois achados fabricados de chegarem ao texto.
>
> **O que este arquivo NÃO é mais.** Até 2026-09-01 o cabeçalho justificava o arquivo pelas métricas de **portabilidade** — "horas até o primeiro treino", "taxa de sucesso de instalação", "número de tentativas". Aquelas métricas pertenciam ao tema de benchmarking, abandonado em 2026-08-26, e **nenhuma hipótese do plano atual as usa**. As contagens de tentativas que aparecem nas entradas abaixo permanecem como registro histórico honesto, mas **não são métricas do TCC** e não devem ser reportadas como tais.
>
> **Regras de preenchimento.** Uma entrada por evento, em ordem cronológica, com data (UTC quando disponível). Registrar falhas com a mensagem de erro literal. Não editar entradas antigas para "limpar" o histórico; correções entram como entrada nova. Distinguir sempre **erro do ambiente** (nosso) de **defeito da plataforma** (dado do TCC) — a confusão entre os dois é o que invalida achado de portabilidade.
>
> **Manutenção (definido em 2026-09-01).** Este arquivo é mantido **pelo assistente**, não pelo aluno. Após cada execução, falha ou decisão relatada em conversa, a entrada correspondente deve ser escrita aqui sem que o aluno precise pedir.
>
> **Nota de escopo (2026-08-26).** O tema do TCC foi reenquadrado neste dia: de "custo de desempenho de backends agnósticos" para **reprodutibilidade em treino de 3DGS** (ver `../pivo-reprodutibilidade-3dgs/PLANO.md`). As entradas anteriores a essa data foram escritas sob o tema antigo, mas o ambiente é o mesmo e permanecem válidas como registro de bring-up.

## Máquina

- Host: `fabio-desktop` (antes `fabio-computer`)
- CPU: AMD Ryzen 7 5700X · RAM: 15 GiB · Disco: 143 GB (122 GB livres)
- GPU: **AMD Radeon RX 9070 XT** (Navi 48, RDNA 4, `gfx1201`, PCI `1002:7550`)
  - Modelo confirmado sem ambiguidade em 2026-08-25 pelo RADV (`deviceName = AMD Radeon RX 9070 XT (RADV GFX1201)`); o PCI ID sozinho não distingue XT / GRE / base

---

## 2026-08-18 — Inventário nº 1 (Ubuntu 26.04)

- **Evento:** primeira execução de `inventario-ambiente.sh`.
- **Saída:** `experimentos/00-inventario/saidas/inventario-fabio-computer-20260818T212900Z.md` (`2026-08-18T21:29:01Z`).
- **Estado:** Ubuntu 26.04 LTS, kernel `7.0.0-29-generic`, Mesa 26.0.3, loader Vulkan 1.4.341, Python 3.14.4. `amdgpu` in-kernel ativo, `/dev/kfd` e `/dev/dri/renderD128` presentes. Nada instalado: sem ROCm, PyTorch, Taichi, pip, gcc, cmake, hipcc, COLMAP, docker.
- **Instrumentação de potência:** `power1_average` = 26,0 W em idle, via `sysfs`/hwmon. Sensor funcional.
- **Tentativas de instalação até aqui:** 0.

## 2026-08-25 — Reinstalação do SO (não era necessária)

- **Evento:** máquina reformatada, de Ubuntu 26.04 para **Ubuntu 24.04.4 LTS** (mídia `20260210`), kernel `7.0.0-30-generic` (HWE).
- **Motivo alegado na ocasião:** que o Ubuntu 26.04 estaria fora da matriz de suporte do ROCm.
- **O motivo era falso.** A matriz do ROCm 7.14.0 (2026-07-16) lista, para gfx1201: `Ubuntu 26.04 (GA kernel: 7.0)`, `Ubuntu 24.04.4 (GA kernel: 6.8)`, `Ubuntu 22.04.5 (GA kernel: 5.15)`. O erro veio de consultar uma página obsoleta (`install-on-linux/.../system-requirements.html`, 2026-07-15) que exibe o aviso *"This page has moved!"*. Detalhes em `bibliografia/verificacao-experimento-rdna4.md` §1.1.
- **Classificação:** **erro do operador**, não defeito da plataforma. Não contabilizar como evidência de imaturidade do stack.
- **Custo:** ~1 dia da janela de execução; perda do estado pré-reinstalação do 26.04 quanto a `dmesg` e `LnkSta` (nunca capturados com root); Mesa e loader Vulkan regrediram (26.0.3 → 25.2.8; 1.4.341 → 1.3.275).
- **Decisão:** não reverter. 24.04.4 também é suportado. Registrada em `PLANO.md` §7.
- **Desvio remanescente a declarar no Cap. 4:** a matriz nomeia `GA kernel: 6.8` para 24.04.4; a máquina roda HWE `7.0.0-30`. Nenhuma combinação literal da matriz descreve o estado atual. Instalar ROCm **sem DKMS**.

## 2026-08-25 — Inventário nº 2 (Ubuntu 24.04.4)

- **Saída:** `experimentos/00-inventario/saidas/inventario-fabio-desktop-20260825T222551Z.md` (`2026-08-25T22:25:51Z`).
- **Estado:** Python 3.12.3 (dentro da faixa suportada pelo ROCm 7.14.0), Mesa 25.2.8, `libvulkan1` 1.3.275, `amdgpu` in-kernel sem DKMS. Toolchain ainda ausente.
- **Potência:** `power1_average` = 9,0 W em idle. Sensor funcional também nesta instalação.
- **Mudança de permissão relevante:** no 24.04.4 o `/dev/kfd` **não** tem ACL POSIX (`crw-rw----`), ao contrário do 26.04. Inclusão em `render` passou a ser obrigatória para ROCm. `card1` e `renderD128` mantêm ACL, então Vulkan funciona sem alteração de grupo.
- **Ressalva sobre a tabela de gates do script:** ela reporta 6/6 reprovados, mas não distingue "NÃO" de "indeterminado por ferramenta ausente", e por isso afirma coisas falsas sobre a plataforma. Corrigir a lógica do resumo antes que essa tabela seja citada em capítulo.

## 2026-08-25 — Gate Vulkan fechado (sucesso, 1ª tentativa)

- **Comando:** `sudo apt install -y vulkan-tools` seguido de `vulkaninfo --summary`.
- **Resultado:**
  - `deviceName = AMD Radeon RX 9070 XT (RADV GFX1201)`, `driverID = DRIVER_ID_MESA_RADV`, `driverInfo = Mesa 25.2.8`
  - `apiVersion` do dispositivo = **1.4.318**; versão de instância do loader = **1.3.275** (degrau irrelevante para o VkSplat, que pede `VK_API_VERSION_1_2`)
  - **`VK_KHR_cooperative_matrix : extension revision 2` — presente**
- **Ressalva de interpretação:** a extensão é fato sobre a *plataforma*. O VkSplat **não** a utiliza (pede `VK_EXT_subgroup_size_control` e `VK_EXT_shader_atomic_float`), logo nenhuma medição do pipeline principal exercita as unidades WMMA.
- **Observação registrada, a enunciar com cuidado:** o RADV emite `WARNING: radv is not a conformant Vulkan implementation, testing use only`, enquanto reporta `conformanceVersion = 1.4.0.0`. Significa que aquele build não passou pela certificação formal da Khronos — **não** que o driver esteja incorreto.
- **Risco de execução identificado:** o `vulkaninfo` enumera `GPU1 = llvmpipe` (rasterizador por software em CPU). Fixar a seleção de dispositivo no protocolo e registrar `deviceName` em toda saída de medição, sob pena de uma rodada cair silenciosamente na CPU.

## 2026-08-25 — Instalação em massa do toolchain: **falha, 1ª tentativa**

- **Comando:**
  ```
  sudo apt install -y build-essential cmake ninja-build pkg-config \
    python3-pip python3-venv python3-dev git-lfs
  ```
- **Erro literal:** `Unable to locate package python3-pip` — e apenas esse pacote, entre os oito da linha.
- **Efeito:** o `apt install` aborta integralmente quando não localiza um pacote, portanto **nenhum** dos pacotes foi instalado.
- **Hipótese 1 (descartada):** `sudo apt update` não executado. A instrução realmente o omitia, mas executá-lo não resolveu.
- **Hipótese 2 (descartada):** componente `universe` desabilitado. Foi dada como confirmada em determinado momento, com base em `sudo add-apt-repository universe` responder *"Adding component(s) 'universe' to all repositories"* e em `apt-cache policy python3-pip` passar a mostrar `Candidate: 24.0+dfsg-1ubuntu1.3`. **A confirmação era espúria:** o `policy` só foi consultado *depois* do `add-apt-repository`, logo não podia distinguir "acabou de ser habilitado" de "já estava habilitado". Permanece indeterminado se `universe` estava ativo antes — e, pela causa real abaixo, é irrelevante.
- **Causa real (confirmada por evidência direta):** o comando foi colado em **uma única linha preservando a barra de continuação** — `... pkg-config \ python3-pip ...`. Com `\` seguido de espaço em vez de quebra de linha, o shell escapa o espaço, que passa a integrar o argumento seguinte. O apt recebeu `" python3-pip"`. A assinatura do defeito é o **espaço duplo** na mensagem, visível na reprodução posterior com outro pacote: `E: Unable to locate package  python3-venv`. Isso explica por que **exatamente um** pacote falhava, e sempre o imediatamente posterior à barra.
- **Classificação:** **erro de digitação/colagem do operador.** Não é defeito da plataforma AMD/ROCm, nem de empacotamento do Ubuntu. Não contabilizar em nenhuma métrica de portabilidade da plataforma.
- **Contagem:** 3 tentativas de instalação do toolchain, 2 malsucedidas — todas atribuíveis ao operador.
- **Nota de método, registrada porque o padrão se repetiu três vezes no mesmo problema:** foram emitidos três diagnósticos sucessivos com confiança acima da evidência disponível — (i) falta de `apt update`, (ii) `universe` desabilitado, e antes disso (iii) a afirmação de que `universe` *estaria* ativo, inferida de `ninja-build` e `git-lfs` não terem falhado. A inferência (iii) estava, no fim, correta, e foi abandonada cedo demais diante de uma saída ambígua. É o mesmo padrão do erro da matriz do ROCm em 2026-08-25: conclusão antes da verificação. **Regra reforçada: exigir a saída literal antes de afirmar causa, e não substituir uma hipótese por outra sem evidência que discrimine entre as duas.**
- **Decisão derivada:** o `python3-pip` foi retirado da lista de dependências — por mérito próprio, não por causa deste erro. No Ubuntu 24.04 o Python do sistema é *externally-managed* (PEP 668), e as dependências do VkSplat serão instaladas em venv (`~/code/tcc/.venv`), que traz o próprio pip via `ensurepip` (pacotes `python3.12-venv`, `python3-pip-whl` e `python3-setuptools-whl`, instalados em 2026-08-25).

---

## 2026-09-01 — Toolchain concluído; build do VkSplat

- **Toolchain instalado** (após a correção do erro de colagem): `build-essential`, `cmake`, `ninja-build`, `pkg-config`, `python3-dev`, `git-lfs`, `libx11-dev`. Venv criado em `~/code/tcc/.venv`. PyTorch instalado a partir do índice de CPU (`download.pytorch.org/whl/cpu`) para evitar o wheel CUDA padrão do PyPI, que arrastaria vários GB de bibliotecas `nvidia-*` inúteis em hardware AMD.
- **Fork:** `harry7557558/vksplat`, commit fixado **`b3ad2b048918496616e0e9346e35c606d813ab55`** (o mesmo auditado em 2026-08-26), clonado em `~/code/tcc/vksplat`.
- **Falha de build, 1ª tentativa:** `pip install -e . --no-build-isolation` na raiz do clone →
  ```
  vksplat does not appear to be a Python project: neither 'setup.py' or 'pyproject.toml' found
  ```
  **Causa:** a estrutura do repositório é aninhada — a raiz contém `README.md`, `CITATION.bib`, `LICENSE`, `compile_shaders.py` e `print_benchmark_results.py`, e o **pacote Python vive em `vksplat/`** (com `setup.py`, `pyproject.toml`, `CMakeLists.txt`, `simple_trainer.py`, `src/`, `slang/`, `shader/`, `viewer/`). Verificado na árvore do commit fixado via API do GitHub. **Classificação: erro do operador** (caminho assumido em vez de verificado).
- **Falha de build, 2ª tentativa:** de dentro de `vksplat/vksplat` →
  ```
  No vulkan sdk found, please install vulkan sdk
  ```
  **Causa:** o `find_vulkan()` do `setup.py` procura, no Linux, o **diretório** `/usr/include/vulkan/` por glob (além de `/usr/local/include/vulkan/` e `~/VulkanSDK/*/x86_64/`). A máquina tinha `libvulkan1` (o loader, vindo do Mesa) mas **não os headers**. **Não é necessário o SDK da LunarG** apesar da mensagem — o pacote da distribuição satisfaz o glob.
  **Classificação: dependência omitida na instrução** — o `libvulkan-dev` constava de uma lista anterior e foi derrubado por engano junto com `glslang-tools`/`spirv-tools`, estes sim desnecessários (os shaders do VkSplat são Slang, com `.spv` pré-compilados no repositório).
- **Resolução:** `sudo apt install -y libvulkan-dev` → build concluída com sucesso.
- **Contagem de bring-up do VkSplat:** 3 tentativas, 2 malsucedidas. Ambas as falhas atribuíveis ao operador/instrução, **nenhuma à plataforma**.
- **Observação de código registrada, esperada e inofensiva:** o `setup.py` monta `library_dirs = os.path.join(vulkan_path, "lib")`, o que com `/usr/include/vulkan/` resulta em `/usr/include/vulkan/lib`, inexistente. O `-lvulkan` resolve pelos caminhos padrão do linker e a build fecha.
- **Pendência de ambiente a registrar no Cap. 4:** o `setup.py` procura GLM em `/usr/include/glm` e, se não achar, **clona a tag `0.9.9.8`** para `third_party/glm`. Confirmar qual caminho foi usado nesta máquina — versão de biblioteca de álgebra entra na descrição de ambiente.

## 2026-09-01 — Dataset Mip-NeRF 360 obtido

- **Fonte:** `http://storage.googleapis.com/gresearch/refraw360/360_v2.zip` (URL oficial extraída da página dos autores). **12.535.427.936 bytes ≈ 11,7 GiB**, `Last-Modified: 2022-03-28`. Servidor aceita `Accept-Ranges: bytes`, logo download retomável com `wget -c`. Não há download oficial por cena isolada.
- **Extraído em** `~/360_v2/`. Estrutura de `garden/` confirmada: `images`, `images_2`, `images_4`, `images_8`, `poses_bounds.npy`, `sparse`. E `garden/sparse/0/` contém `cameras.bin`, `images.bin`, `points3D.bin` — formato COLMAP binário, que é o único que o VkSplat lê.
- **Achado que afeta H4 (comparabilidade com valores publicados):** o `benchmark_mipnerf360()` do VkSplat aponta as cenas outdoor para **`images_4_png`**, com o comentário literal dos autores *"In the paper, we benchmark on PNG images generated by GSplat"*. O dataset oficial traz **JPEG** em `images_4`. Portanto os números publicados **não** foram obtidos sobre as imagens que este experimento vai usar. JPEG × PNG altera o PSNR absoluto. **Declarar como limitação no pré-registro; não comparar valores absolutos com o artigo sem essa ressalva.**

## 2026-09-01 — `simple_trainer.py` não tem parsing de argumentos

- **Descoberto ao executar `python simple_trainer.py --help`**, que ignorou a flag e executou o treino: o bloco `__main__` é literalmente `train_main(MCMCTrainerConfig())`, com `train_main(TrainerConfig())` comentado. **Não existe `argparse`, `tyro` ou equivalente.** A configuração é a dataclass `TrainerConfig`, com defaults codificados para a máquina do autor (`/mnt/d/gs/data/360_v2/bicycle`, `/mnt/d/gs/outputs` — caminhos WSL).
- **Erro literal resultante:**
  ```
  vksplat.RuntimeError: cameras.bin or cameras.txt not found in `/mnt/d/gs/data/360_v2/bicycle/sparse/0/`
  ```
- **Decisão de método:** em vez de editar os defaults de `simple_trainer.py`, foi criado um runner separado, `~/code/tcc/vksplat/vksplat/tcc_runner.py`, que importa o módulo e sobrescreve os campos. **Motivo:** manter `simple_trainer.py` intocado para que o patch **D1** da escada de ablação (semear `random.shuffle`) seja o *único* diff naquele arquivo, preservando a limpeza dos commits do experimento.
- **Seleção de dispositivo:** existe embutida — `TRAIN_DEVICE` no topo do módulo, `-1` = auto. Fixado em `0` no runner. Preferível à variável de ambiente `MESA_VK_DEVICE_SELECT` sugerida antes.

## 2026-09-01 — **N0 alcançado: primeiro treino de 3DGS em RDNA 4**

> Este é o nível N0 de evidência do `PLANO.md` §2.4, e **é resultado publicável por si**: o README do VkSplat lista como testadas RTX 3090, RTX 4080 Super, RTX 5070 Laptop, **AMD RX 7800 XT (RDNA 3)** e Intel UHD 750/770. **RDNA 4 não consta.** Este é, pelo que se sabe, o primeiro treino documentado do VkSplat em `gfx1201`.

- **Configuração:** `MCMCTrainerConfig` (entrypoint padrão), `cap_max = 1.000.000`, cena `garden`, `image_dir = images_4` (JPEG), `eval_interval = 8`, **`train_steps = 500`** (smoke test), `TRAIN_DEVICE = 0`.
- **Enumeração de dispositivos, saída literal:**
  ```
  Device Requirement: subgroup>=32, maxGroups>=[786432 256 1], maxThreads>=[1024 16 1], maxShared>=21712, I16|I64|F32Atomic
  [0] AMD Radeon RX 9070 XT (RADV GFX1201) - VIABLE
    subgroup=64, maxGroups=[4294967295 65535 65535], maxThreads=[1024 1024 1024], maxShared=65536, I16|I64|F32Atomic
  [1] llvmpipe (LLVM 20.1.2, 256 bits) - NOT VIABLE
    subgroup=8, maxGroups=[65535 65535 65535], maxThreads=[1024 1024 1024], maxShared=32768, I16|I64|F32Atomic
  Using device [0]
  ```
- **`F32Atomic` presente e dispositivo VIABLE** — a pré-condição de H3a está confirmada no hardware real. **Não** houve mensagem pedindo `USE_EMULATED_INT64` ou `USE_EMULATED_F32_ATOMIC`, logo o caminho usa atômicas em float **nativas**, não a emulação por laço CAS.
- **Risco de `llvmpipe` auto-mitigado:** o próprio VkSplat rejeita o dispositivo 1 por `subgroup=8 < 32`. O risco registrado em `PLANO.md` §8 pode ser rebaixado — mas continuar registrando `deviceName` por execução.
- **Cena:** 185 imagens, **161 treino / 24 validação**, 138.766 pontos iniciais, `Scene scale: 1.226526`.
- **Desempenho do smoke test:** 500 passos em **3,1 s** (161,01 it/s). `Num splats` final = 138.766 — inalterado, porque `refine_start_iter = 500` e a densificação não começou.
- **VRAM:** 638,5 MiB total, pico igual. Maiores consumidores: `g_sh_coeffs_1` e `g_sh_coeffs_2` com 183,1 MiB cada — escalam com o número de gaussianas, logo a estimativa para 1M splats é ordens acima.
- **Métricas em 500 passos** (sem significado de qualidade, o modelo está subtreinado): PSNR 18,98 · SSIM 0,504 · LPIPS VGG 0,509 · LPIPS Alex 0,580.
- **Avaliação:** 24 imagens de validação em **1 min 04 s**, em CPU (não há CUDA; o código faz `device = "cuda" if torch.cuda.is_available() else 'cpu'`). Pesos do AlexNet baixados sob demanda, 233 MB, agora em cache.
- **Tempo até o primeiro treino bem-sucedido:** primeiro inventário em 2026-08-18, primeiro treino em 2026-09-01 — **14 dias de calendário**, com uma reinstalação de SO desnecessária e um reenquadramento de tema no meio. O tempo de trabalho efetivo é muito menor e não foi cronometrado; **reportar o número de calendário sem qualificação seria enganoso.**

### Achado: o escalonador Thompson alterna kernels dentro de uma única execução

O `timing breakdown` do smoke test registra, em 500 passos:

```
RasterizeBackward                         - 500, 1.653 secs
_RasterizeBackwardScheduling_Tensor_0_8_8 - 235, 1.355 secs
_RasterizeBackwardScheduling_PerSplat     - 265, 0.298 secs
```

- **Confirmação empírica direta da fonte de não-determinismo D2.** A auditoria de 2026-08-26 mostrou que, em AMD, o `ThompsonSamplingScheduler` alterna entre `PerSplat` (autodiff) e `Tensor_0_8_8` (formulação em espaço-log), que **não são numericamente equivalentes**. Aqui isso é observado em execução: 235 passos com um kernel, 265 com o outro, **na mesma execução**.
- **Custo por chamada:** `PerSplat` ≈ 1,12 ms; `Tensor_0_8_8` ≈ 5,77 ms — cerca de 5× mais lento. O escalonador ainda escolheu o lento em 47% dos passos porque em 500 passos o Thompson sampling está na fase de exploração. **Logo a proporção da mistura depende do comprimento da execução e das latências medidas, e varia entre execuções.**
- **Consequência operacional:** registrar as duas contagens em toda execução; elas são dado, não diagnóstico. O patch **D2** (`RASTERIZE_BACKWARD_USE_SCHEDULING 0` em `src/config.h:24`) fixa `PerSplat` e elimina esta fonte.
- Nota de leitura do breakdown: itens com prefixo `_` são excluídos do `Total` pelo próprio código (`if not item.startswith('_')`), então o `1,653 s` de `RasterizeBackward` já é a soma dos dois.

### Achado: as duas métricas LPIPS não estão sob a mesma convenção

No `eval()` de `simple_trainer.py`:

```python
lpips_vgg_fun  = LearnedPerceptualImagePatchSimilarity(net_type="vgg",  normalize=False)
lpips_alex_fun = LearnedPerceptualImagePatchSimilarity(net_type="alex", normalize=True)
```

As imagens são carregadas em `[0,1]`. Com `normalize=False` o `torchmetrics` espera `[-1,1]`, logo **`lpips_vgg` é calculado sob a convenção errada** — instância concreta do defeito herdado do pipeline do 3DGS documentado no Apêndice B do FreeTimeGS++. O `lpips_alex`, com `normalize=True`, está correto. **Reportar as duas declarando a convenção de cada uma; não comparar `lpips_vgg` com valores de terceiros sem verificar a convenção deles.**

### Próximo passo definido

1. Execução **completa** (`train_steps = 30000`, remover o override do runner), para obter o tempo real. **Não extrapolar de 161 it/s** — a densificação MCMC cresce até 1M gaussianas e o custo por passo sobe com o número de splats, junto com a VRAM.
2. Registrar: `Time elapsed`, tempo de parede com avaliação, `Num splats` final, `Peak (queried)` de VRAM, pico de RAM do host, e as contagens dos dois kernels.
3. Rodar a completa também com `TrainerConfig` (densificação ADC original), para ter o custo das duas antes de fixar a estratégia no pré-registro. **Recomendação em aberto:** ADC para o baseline, porque a MCMC injeta ruído SGLD e relocação aleatória a cada passo, misturando estocasticidade algorítmica ao não-determinismo de execução — que é a distinção que sustenta a originalidade do trabalho.
4. Com o tempo real em mãos, dimensionar **N** (repetições por degrau da escada D0–D3) e escrever o pré-registro.

### Estado do cronograma

A janela do Sprint 0 no `PLANO.md` §4 era 26/ago → 02/set. **N0 foi alcançado em 01/set, dentro da janela.** Restam do Sprint 0: auditar `morton_sort.slang` (determinismo da reordenação periódica, que pode falsificar H3a) e `print_benchmark_results.py` (metodologia das 5 execuções do artigo).

---

## 2026-09-01 — Execução completa nº 1 (MCMC, `garden`, 30k passos)

- **Log bruto:** `~/code/etc/logs/log1.txt` (582 linhas). Work dir da execução: `20260901_223829`.
- **Configuração:** `MCMCTrainerConfig`, cena `garden`, `image_dir = images_4` (JPEG), `eval_interval = 8`, `train_steps = 30000`, `TRAIN_DEVICE = 0`.
- **Execução limpa.** Único aviso em todo o log: `WARNING: radv is not a conformant Vulkan implementation, testing use only.` **Não** houve menção a `USE_EMULATED_INT64`, `USE_EMULATED_F32_ATOMIC`, "Shaders must be compiled with", "a backward implementation is disabled due to hardware limitation", exceções ou tracebacks. Confirma-se: atômicas em float **nativas**, sem emulação por CAS, e nenhuma implementação de backward desabilitada por limite de memória compartilhada.

### Tempos

| Fase | Tempo |
|---|---|
| Treino (30.000 passos) | **292,2 s** (`04:52`, média **102,69 it/s**) |
| Rendering val (24 imagens) | ~1,6 s |
| Saving val (24 imagens) | ~0,4 s |
| **Eval** (PSNR/SSIM/LPIPS, 24 imagens, **em CPU**) | **~63,8 s** |
| **Parede, somando as fases medidas** | **≈ 356 s (~5 min 56 s)** |

**A taxa não é constante:** ~200–220 it/s no início e ~95–100 it/s depois de saturar 1M gaussianas. Isso invalida qualquer extrapolação a partir do smoke test de 500 passos, que rodava a 161 it/s com os 138.766 pontos iniciais.

**Ausências no log, a considerar na estimativa:** não há tempo registrado para leitura do COLMAP e carga das 185 imagens, nem para `Writing PLY`. O parede real é maior que 356 s por margem não medida. Para dimensionamento, usar **7 minutos por execução** como estimativa conservadora.

### Resultado

- `Num splats: 1000000` — saturou o `cap_max`. Evidência no log: a partir de certo ponto as linhas de densificação viram `13975 relocate, 23152 add -> 1000000 splats` com `add` caindo a zero. (O valor de `cap_max` não é impresso; foi inferido da saturação.)
- `VRAM usage: 0.88 GiB`; `Peak (queried) = 898,4 MiB`. Numa placa de 16 GB, **VRAM não é restrição**. Maiores buffers: `g_sh_coeffs_1`, `g_sh_coeffs_2` e `sh_coeffs`, 183,1 MiB cada.
- **Métricas:** PSNR **26,95** · SSIM **0,846** · LPIPS VGG **0,143** · LPIPS Alex **0,113**.
  - Lembrar que `lpips_vgg` é calculado com `normalize=False` sobre imagens em `[0,1]` — convenção incorreta herdada do pipeline do 3DGS. Só `lpips_alex` está sob a convenção pretendida.
  - **Não comparar o PSNR com os valores publicados do artigo** sem as duas ressalvas já registradas: é **uma** cena (não média de 7) e as imagens são **JPEG** de `images_4`, não os PNG gerados pelo gsplat que os autores usaram.
- **RAM do host não foi medida**, mas a execução concluiu com `image_cache_device` no padrão (`'cpu'`), logo o cache do dataset em RAM caberia nos 15 GiB para `garden`/`images_4`. **O risco de OOM registrado no `PLANO.md` §8 pode ser rebaixado para esta configuração** — reavaliar se outra cena ou resolução entrar no escopo.

### Timing breakdown completo

| Item | Contagem | Segundos |
|---|---|---|
| RasterizeBackward | 30000 | 91,103 |
| `_RasterizeBackwardScheduling_PerSplat` | **29456** | 84,935 |
| FusedProjectionBackwardOptimizerStep | 30000 | 79,812 |
| CopyTrainImageToDevice | 30000 | 45,952 |
| RasterizeForward | 30000 | 20,250 |
| ProjectionForward | 30000 | 12,734 |
| ComputeSSIMGradient | 30000 | 11,380 |
| `_RasterizeBackwardScheduling_Tensor_0_8_8` | **544** | 6,174 |
| MCMCPostBackward | 30000 | 5,992 |
| SortRTS | 30300 | 5,863 |
| GenerateKeys | 30000 | 5,479 |
| CalculateIndexBufferOffset | 30000 | 1,744 |
| `_Cumsum` | 30285 | 1,023 |
| ComputeTileRanges | 30000 | 0,362 |
| `_Sum` | 244 | 0,010 |
| **Total** | — | **280,671 / 292,152** |

### Achado: a mistura do escalonador depende do comprimento da execução

`29456 + 544 = 30000` — exatamente uma escolha de kernel por passo. Proporção:

| Execução | `PerSplat` | `Tensor_0_8_8` |
|---|---|---|
| Smoke test, 500 passos | 265 (53,0%) | 235 (47,0%) |
| Completa, 30.000 passos | **29.456 (98,19%)** | **544 (1,81%)** |

Custo por invocação nesta execução: `PerSplat` 2,883 ms; `Tensor_0_8_8` 11,349 ms — 3,9× mais lento. O Thompson sampling converge para o kernel rápido, mas **só depois de gastar centenas de passos explorando o lento**. Consequências para o experimento:

1. A contaminação de D2 numa execução completa é de **~1,8% dos passos**, não ~47% como o smoke test sugeria. Menor do que se temia, mas **não nula**, e esses 544 passos usam formulação numérica diferente.
2. **A contagem varia entre execuções**, porque a convergência do escalonador depende de latências medidas, que dependem da carga da máquina. Registrar as duas contagens em toda execução — é dado, não diagnóstico.
3. `FusedProjectionBackwardOptimizerStep` custa 79,8 s, quase tanto quanto `RasterizeBackward` (91,1 s) — mas a auditoria mostrou que aquele kernel roda uma thread por gaussiana com índices disjuntos, **sem atômicas**. Logo é determinístico e não é candidato a fonte de divergência.

### Dimensionamento de N

Com ~7 min por execução (estimativa conservadora, incluindo margem para as fases não medidas):

| N por degrau | Execuções (4 degraus) | Tempo de máquina |
|---|---|---|
| 20 | 80 | ~9 h |
| **30** | **120** | **~14 h** |
| 50 | 200 | ~23 h |

**O experimento não é limitado por compute.** N = 30 por degrau é folgado no cronograma e dá precisão razoável na estimativa do desvio-padrão, que é a quantidade central do trabalho. Fixar no pré-registro, com a justificativa estatística ancorada em Hoefler e Belli (leitura ainda pendente).

Nota: a fase de avaliação consome 63,8 s dos 356 s (18%) e roda em CPU. Não é otimizável sem trocar a métrica, e PSNR é a métrica primária — manter.

---

## 2026-09-01 — Execução completa nº 2 (ADC / `default`, `garden`, 30k passos)

- **Log bruto:** `~/code/etc/logs/log2.txt` (396 linhas). Work dir: `20260901_225632_garden`.
- **Configuração:** `TrainerConfig` (densificação ADC original do Inria), mesma cena, `images_4`, 30.000 passos, `TRAIN_DEVICE = 0`.
- **Execução limpa.** Novamente o único aviso é o de não-conformidade do RADV. Nenhum `USE_EMULATED_*`, nenhuma implementação de backward desabilitada, zero exceções.
- **Estratégia confirmada como `default`:** `DefaultPostBackward - 30000` no timing; buffers `default_grad`, `default_keep_mask`, `default_radii`, `default_dupli_mask`, `default_split_mask` no VRAM breakdown; vocabulário `dupli / split / prune / reset opacity`. Nenhuma ocorrência de `MCMC`, `mcmc_*` ou `relocate`.

### Comparação direta entre as duas estratégias

| | MCMC (`cap_max` 1M) | ADC (`default`) | Razão |
|---|---|---|---|
| Treino | 292,2 s | **839,8 s** | 2,9× |
| Taxa final | 102,69 it/s | 35,72 it/s | — |
| Parede (com eval) | ≈ 356 s | **≈ 910 s** | 2,6× |
| Gaussianas finais | 1.000.000 (saturado) | **5.830.929** | 5,8× |
| VRAM `Total (queried)` | 898,4 MiB | 5.849,5 MiB | 6,5× |
| **VRAM `Peak (queried)`** | 898,4 MiB | **6.909,4 MiB** | 7,7× |
| PSNR | 26,95 | **27,37** | +0,42 dB |
| SSIM | 0,846 | 0,863 | — |
| LPIPS VGG | 0,143 | 0,108 | — |
| LPIPS Alex | 0,113 | 0,077 | — |

**A comparação não é pareada e não deve ser reportada como se fosse.** A MCMC estava limitada a 1M gaussianas por `cap_max`; a ADC cresceu sem teto até 5,83M. A vantagem de qualidade da ADC é largamente explicada por **5,8× mais primitivas**, não pela estratégia em si. O próprio `benchmark_mipnerf360()` do VkSplat trata a ADC como o caso "sem teto" (`cap_max = None`). Para comparar estratégias seria preciso igualar o orçamento de gaussianas.

### Evolução da densificação (ADC)

144 eventos de densificação, a cada ~100 passos, cessando por volta do passo 15.000 — o `Num splats` final é idêntico ao do último evento, logo **não há mudança de contagem entre o passo ~15.000 e o 30.000**.

- Primeiro evento: `4194 dupli, 3265 split, 497 prune -> 145728 splats`
- Meio: `42004 dupli, 1580 split, 2770 prune -> 4790986 splats`
- Último: `15185 dupli, 1109 split, 1717 prune -> 5830929 splats`

Quatro eventos `reset opacity` (aprox. passos correspondentes às linhas 70, 132, 194, 256 do log), cada um seguido de poda massiva — quedas de 2,1M, 4,3M, 5,3M e 5,7M gaussianas respectivamente. A razão `dupli/split` cresce de ~1,3 para ~13,7 ao longo do treino.

### Perfil de custo é qualitativamente diferente

Na ADC, o item mais caro **não** é o backward de rasterização:

| Item | MCMC | ADC |
|---|---|---|
| `FusedProjectionBackwardOptimizerStep` | 79,8 s | **428,0 s** |
| `RasterizeBackward` | 91,1 s | 189,9 s |

O `FusedProjectionBackwardOptimizerStep` escala com o número de gaussianas (uma thread por gaussiana) e passa a dominar. **Isso é relevante para a atribuição:** aquele kernel foi auditado e **não tem atômicas** — índices disjuntos, sem contenção. Logo, na ADC, mais da metade do tempo de treino é gasto num estágio determinístico.

### O escalonador se comporta igual nas duas

| Execução | `PerSplat` | `Tensor_0_8_8` |
|---|---|---|
| MCMC, 30k | 29.456 (98,19%) | 544 (1,81%) |
| ADC, 30k | 29.464 (98,21%) | **536 (1,79%)** |

A proporção é praticamente idêntica, o que é consistente com a fase de exploração do Thompson sampling ter comprimento fixo em passos, não em tempo. Mas as contagens **diferem** (544 × 536) entre duas execuções de configurações distintas — indício de que variam também entre execuções da mesma configuração, o que é exatamente o que D2 vai medir. Registrar sempre.

### Decisão: ADC como configuração do experimento

Adotar **`TrainerConfig` (ADC)** para a escada de ablação D0–D3. Razões, em ordem de força:

1. **A contagem de gaussianas passa a ser um observável que varia.** Na ADC as decisões de `dupli`/`split`/`prune` são **comparações de limiar sobre gradientes** (`grow_grad2d = 0.0002`, `prune_opa = 0.005`). Uma diferença numérica ínfima na acumulação atômica pode inverter uma comparação, o que muda discretamente o número de primitivas e amplifica a divergência de forma macroscópica. Isso dá um **segundo canal de evidência**, discreto e fácil de reportar, além das métricas de imagem — e responde diretamente à sub-pergunta 2 do `PLANO.md` §2.1 (a dispersão aparece nos parâmetros do modelo?).
2. **A MCMC com `cap_max` suprime justamente esse canal**, porque fixa a contagem final em exatamente 1M. Dispersão de contagem fica invisível por construção.
3. **É a densificação canônica do 3DGS original**, logo o achado generaliza para o algoritmo de referência em vez de para uma variante.
4. Custo continua trivial: 910 s por execução → 4 degraus × N=30 = **~30 h de máquina**. VRAM de pico 6,9 GiB, folgada nos 16 GB.

**Adição recomendada, barata:** rodar o degrau **D0 também em MCMC** (30 execuções ≈ 3 h) como comparação secundária. Serve para testar se fixar a contagem por `cap_max` suprime ou apenas esconde a dispersão — pergunta interessante que custa 3 horas.

**Correção de justificativa registrada:** em 2026-09-01 eu havia recomendado ADC alegando "menos aleatoriedade interna que a MCMC". A auditoria mostra que **as duas usam RNG** — a ADC em `default.slang`, fase `Split` (`randn3(uniforms.seed, id_src)`), e ambas semeadas a partir de `rng(42)`, com gerador *counter-based* determinístico. A justificativa correta é a do item 1 acima, não a redução de aleatoriedade.

---

## 2026-09-02 — Auditoria da reordenação Morton: **quarta fonte de não-determinismo, e a mais consequente**

Auditoria de código no commit fixado `b3ad2b0`. O resultado muda a escada de ablação de quatro para cinco degraus — **antes** de o pré-registro ser commitado.

### O achado

`vksplat/slang/morton_sort.slang`, fase **`ComputeStats`** (linhas 58-70), tem **6 sítios próprios de `InterlockedAddF32`** — acumulação em `float32` de média e variância das posições das gaussianas, por redução entre workgroups, **sem ordem imposta**:

```
stats.InterlockedAddF32(0*sizeof(float), mean.x);
...
stats.InterlockedAddF32(5*sizeof(float), mean2.z);
```

Há pré-redução por `WaveActiveSum` e `groupshared`, logo é **uma** atômica por workgroup por componente. Com `num_splats <= 1024` haveria um único workgroup e a soma seria determinística; acima disso — sempre, em cena real — fica sujeita à ordem de chegada.

**O mecanismo de amplificação é uma função degrau.** A fase `GenerateKeys` normaliza a posição por essas estatísticas e quantiza com `uint32_t(pos.x * (float)(1 << 10) + 0.5f)` — 10 bits por eixo, chave de 30 bits. Média ou desvio diferindo no último bit alteram a posição normalizada, e **qualquer gaussiana próxima de fronteira de voxel cai em célula vizinha** → chave Morton diferente → **permutação diferente do array inteiro**. Sem suavização.

### Por que isso ameaçava o plano

Citação literal do relatório: *"Isto é independente do backward. Mesmo que os 9 sítios de `_ATOMIC_ADD` em `alphablend_shader_bwd_per_splat.slang` fossem tornados determinísticos, `ComputeStats` continuaria não-determinístico. A intervenção planejada no backward não cobre este sítio."*

Ou seja: **H3a, na formulação anterior, nasceria refutada.** O degrau que patcheava só o backward não poderia produzir execuções bit-idênticas, e o motivo apareceria na semana 6 em vez de agora.

A reordenação também **remapeia os `splat_id` de destino** das atômicas do backward — aplica a mesma permutação a `sh_coeffs`, `xyz_ws`, `rotations`, `scales_opacs`, aos buffers de gradiente e ao estado do Adam. Altera portanto o padrão de colisão dessas atômicas: é fonte independente **e a montante**.

### Consequência: escada de cinco degraus

D3 passa a ser "desativar a reordenação Morton" (`#if 1` → `#if 0` em `gs_trainer.cpp:1050` e `:1264`; **não há flag, campo de config nem variável de ambiente**), e a intervenção em ponto fixo vira **D4**. Registrado em `../pivo-reprodutibilidade-3dgs/pre-registro.md` §3.1, com H3 desdobrada em H3.1–H3.4, uma por degrau.

**H3.3 — "desativar a reordenação Morton reduz a dispersão" — é hipótese nova, criada por esta auditoria, e nenhum trabalho localizado a considera.**

### Inventário completo de atômicas em `float32`

Varredura dos 18 arquivos de `vksplat/slang/`:

| Arquivo | Sítios |
|---|---|
| `alphablend_shader_bwd_per_splat.slang` | 9 |
| `alphablend_shader_bwd_per_pixel.slang` | 9 |
| `alphablend_shader_bwd_tensor.slang` | 9 |
| **`morton_sort.slang`** | **6** |
| `ssim.slang`, `utils.slang` e os 12 restantes | **0** |

Como há três variantes de backward e o escalonador em AMD alterna entre `PerSplat` e `Tensor_0_8_8`, o patch de D4 cobre só `PerSplat` — **suficiente porque D2 é cumulativo e fixa essa variante.** Propriedade do desenho, a declarar no texto.

### Verificado como determinístico

- **Radix sort:** ranking por `subgroupBallot` com desempate pelo índice anterior; atômicos só inteiros em memória compartilhada; `barrier()` por iteração. Permutação única dadas as chaves.
- **Compactação de poda da ADC:** prefix-sum inteiro (`cumsum.slang` → `where.slang`), estável.
- **Apêndice de dupli/split:** índices-fonte em ordem crescente de `gid`, sem atômica de append.
- **Densificação MCMC:** atômicos **inteiros** de contagem; índices por busca binária sobre `hash_u32_u64(seed, tid)`, função pura.
- **`ssim.slang`:** acumula em `groupshared` com barreira, uma escrita por thread, sem redução entre workgroups.

### Alcance temporal do Morton

A condição de execução (`step % config.refine_every == 0`) é **mais frouxa** que a da densificação: roda antes de `refine_start_iter` e inclusive em `step == 0`. Na ADC há `return` antecipado em `step >= refine_stop_iter` que a curto-circuita; **na MCMC não há**, e ela roda até o fim do treino. Coerente com a densificação ADC cessar por volta do passo 15.000.

### Possível defeito upstream, a verificar

`gs_trainer.cpp:1390-1391` chama `applyIndex(buffers.default_radii, 2)` e `applyIndex(buffers.default_grad, 2*2)` — *strides* 2 e 4 — enquanto os buffers são alocados como `num_splats` e `2*num_splats` floats, ou seja 1 e 2 por gaussiana. No caminho de poda o *stride* é derivado do tamanho real; aqui está fixo. **Não verificado** se `resizeDeviceBuffer` arredonda a alocação de modo a tornar isso inócuo (`buffer.cpp` não lido). Se for defeito real, é reportável upstream e vira achado próprio.

### Não verificado

`buffer.cpp`; encadeamento de passes de `executeSort` no host; `upsweep.comp` e `spine.comp` do radix sort; e a **magnitude empírica** com que a divergência de `stats` se converte em chaves Morton distintas — que é justamente o que o degrau D3 vai medir.
