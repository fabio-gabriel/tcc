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

---

## 2026-09-02 — Pré-registro, estágio 1, commitado

- **Commit `879dc8751e9c3d229506028600998840f24bb227`** no repositório do TCC. Protocolo de D0 a D3 travado: configuração, grandezas, plano estatístico, critérios de refutação, política de retenção.
- Estágio 2 (degrau D4) deixado como rascunho, por depender da toolchain Slang e da medição de magnitude dos gradientes.
- **Fork:** `github.com/fabio-gabriel/vksplatTCC`, branch `tcc-base`, com `upstream` em `harry7557558/vksplat`. Licença Apache-2.0.

| Degrau | SHA | Patch |
|---|---|---|
| D0 | `3a5c0d97a6790e07ebd011a116d4d016c957ab9f` | apenas harness, nenhuma ablação |
| D1 | `4cb921a82f686c68578978bdeb215057935ae048` | `random.seed(step)` descomentado |
| D2 | `b395759efaeff12846aca49af1e8c9ca1aab02ac` | `RASTERIZE_BACKWARD_USE_SCHEDULING 0` |
| D3 | `d222c47182f5917be0cc209f19d3257e1ebad17e` | `#if 1`→`#if 0` nas duas chamadas a `executeMortonSorting` |

- **Armadilha registrada em `pre-registro.md` §3.2:** o `.so` compilado não é versionado (`*.so` no `.gitignore`), logo `git checkout` de outro degrau **não troca o binário**. Mitigação: `run_degree.sh` recompila **incondicionalmente** após cada checkout. É o modo de falha silencioso do protocolo.

## 2026-09-08 — Depuração do harness: quatro tentativas até a checagem de dispositivo funcionar

Registrado porque é caso exemplar da regra de método do projeto, e porque o desperdício foi real: **cada tentativa custou ~15 min**, já que a checagem roda no fim da execução.

| Tentativa | Padrão | Resultado | Causa |
|---|---|---|---|
| 1 | `grep -q 'Using device \[0\]'` | falhou | barra invertida perdida na colagem; `[0]` virou classe de caracteres em BRE |
| 2 | `grep -qF 'Using device [0]'` | falhou | `-F` correto, mas os bytes reais não são os supostos |
| 3 | extração por `tr -dc '0-9'` | falhou, retornou `00` | ver abaixo |
| 4 | limpa ANSI, então extrai | **funciona** | — |

**Causa raiz, revelada por `cat -A`:** a linha é literalmente

```
Using device [^[[0m0^[[m]$
```

O índice vem embrulhado em **códigos de escape ANSI** (`ESC[0m` … `ESC[m`). O VkSplat colore a saída — coerente com `printf("\033[91m%s\033[m\n", ...)` em `src/config.h`. A extração por dígitos capturava o `0` de `[0m` **e** o índice, produzindo `00`.

**Lições registradas:**

1. **Nunca casar string formatada de saída de programa.** Extrair valor, limpando ANSI antes.
2. **`cat -A` primeiro.** As três primeiras tentativas foram chutes; a quarta veio de olhar os bytes.
3. **Os logs do VkSplat contêm ANSI.** Qualquer análise que leia log, e não JSON, tem de limpar. Princípio adotado: **o log arquivado permanece bruto** — é o registro primário; a limpeza acontece na leitura.
4. O canal de transferência por colagem estava **removendo caracteres** (barras invertidas e asteriscos). Solução adotada: transferência pelo git, com `sha256sum` conferido nas duas pontas.

### Execuções descartadas

Quatro execuções completas de ADC foram produzidas antes do harness estar válido e **não contam como dado**: a de 2026-09-01 (`log2.txt`) e três de 2026-09-08. Descarte declarado para que a contagem de execuções do TCC não fique inflada. Sinal que já apareceu nelas e antecipou H1: gaussianas de 5.767.196 a 5.874.753 (amplitude 1,8%) e PSNR de 27,36 a 27,40.

## 2026-09-08/09 — Séries D0 a D3 executadas, N=20 por degrau

> **Nota acrescentada em 2026-09-21, não edição silenciosa:** o título e os números de N=20 desta entrada **não são todos de 09-08/09**. O segundo bloco de D3 (`run010`–`run019`) só foi executado em **2026-09-20/21**, sob kernel diferente. Esta entrada foi redigida em 2026-09-21 e consolidou os números finais sob a data da primeira metade, o que apaga essa distinção. Ver a entrada **"2026-09-21 — Auditoria dos dados em disco"** ao final deste caderno.

Orquestradas por `run_degree.sh`, em **blocos intercalados de 10**. Dados em `pivo-reprodutibilidade-3dgs/dados/<degrau>/`, com `manifest.tsv` de hashes.

**Decisão de sequenciamento (2026-09-09):** a ordem dos degraus **não** está pré-registrada. Adotados blocos intercalados de 10 em vez de completar um degrau por vez, por dois motivos: dá atribuição cedo, e evita confundir o efeito do degrau com fatores que variem no tempo (carga, deriva térmica). É a recomendação de Hoefler e Belli — não alinhar o que não se consegue fixar.

### H1 — **confirmada de forma categórica**

**80 execuções, 80 hashes de `splat.ply` distintos.** 20 em cada degrau, zero repetição em qualquer um. Não é resultado estatístico: é identidade bit a bit, e falhou 80 de 80.

**O ponto mais importante é que H1 sobrevive a D1.** Com `random.seed(step)` ativo, a ordem de visitação das imagens é determinística — e o modelo continua diferente em toda execução. Isso **elimina a explicação mundana** ("é só o embaralhamento não semeado"), que era a objeção mais previsível em banca. O não-determinismo é intrínseco ao pipeline.

E sobrevive a D2 e D3. Com seed fixa, kernel fixo e Morton desligado, ainda há 20 modelos distintos em 20 execuções. **Resta a acumulação atômica em `float32` do backward — alvo de D4.**

### Dispersão por degrau, PSNR, N=20

| | mediana | IQR | MAD | amplitude | pares ≥ 0,10 dB | tempo (mediana) |
|---|---|---|---|---|---|---|
| **D0** baseline | 27,3614 | 0,0507 | 0,0280 | 0,1905 | **27/190 = 14,2%** | 833,7 s |
| **D1** +seed | 27,3849 | 0,0331 | 0,0119 | 0,1303 | 6/190 = 3,2% | 836,7 s |
| **D2** +kernel fixo | 27,3803 | 0,0442 | 0,0201 | 0,1803 | 16/190 = 8,4% | 826,3 s |
| **D3** +sem Morton | 27,3900 | **0,0214** | **0,0091** | 0,0882 | 0/190 = 0,0% | **942,4 s** |

IQR de gaussianas: D0 37.813; D1 18.909; D2 15.799; D3 17.377.

### H2 — sustentada

Estatística pré-registrada: **fração de pares com |ΔPSNR| ≥ 0,10 dB, sobre D0**. Resultado **17,8% em N=10 e 14,2% em N=20**, contra critério de ≥ 5%. **H2 sustentada.**

A escolha da fração de pares em vez da amplitude se justificou: a amplitude de D0 subiu de 0,1626 para 0,1905 dB ao dobrar N — como previsto, porque amplitude não é estimador estável — enquanto a fração ficou na mesma ordem.

**Contexto que dá peso:** o limiar de 0,10 dB veio do levantamento de 2026-08-26. O gsplat declara **paridade** com o 3DGS a +0,05 dB e apresenta features com +0,03, +0,11 e +0,18 dB; o Mip-Splatting reporta +0,09 dB contra seu próprio 3DGS retreinado. **A dispersão entre execuções idênticas do código como distribuído excede esses ganhos publicados.**

### Verificações de sanidade

- Commits uniformes por degrau, conferidos via `env.json`.
- Escalonador em D0 e D1: `PerSplat` 29.463–29.465, `Tensor_0_8_8` 535–537 — **notavelmente estáveis**, confirmando a expectativa pré-registrada de efeito pequeno em D2. Em D2 e D3, contagens **0/0**, confirmando que o patch funcionou.
- A mediana de PSNR varia só 0,029 dB entre os quatro degraus, dentro da dispersão intra-degrau. **As intervenções mexem em escala, não em posição** — exceto D3, que paga em tempo.

### Custo do determinismo: D3 é 14% mais lento

942,4 s contra 826,3 s de D2. Desligar o Morton destrói o *coalescing* que ele existe para prover — `src/config.h` comenta *"reordering for better memory colaescing"*.

**Observação de engenharia, candidata a trabalhos futuros ou a degrau extra:** desligar o Morton é a forma **ingênua** de obter determinismo. Tornar determinística apenas a fase `ComputeStats`, com 6 atômicas, provavelmente custaria perto de zero e preservaria a localidade. Técnicas em Demmel e Nguyen; Collange et al.

## 2026-09-09 — Erro no plano estatístico, desvio declarado, e resultado dos testes

### O erro

O `pre-registro.md` §5, commitado em `879dc87`, mandava comparar degraus por **CIs da mediana não sobrepostos** e **Kruskal-Wallis**. Ambos testam **localização**. Mas H3.1 a H3.4 afirmam redução de **dispersão**. Os testes especificados são incapazes, em princípio, de estabelecer a afirmação do trabalho, e nenhum aumento de N corrige. **Erro de especificação, não de execução.**

Confirmação empírica de que a mediana não é o canal: medianas diferem em 0,029 dB entre degraus, dentro da dispersão intra-degrau, enquanto os IQRs vão de 0,0214 a 0,0507.

### O desvio declarado

Commit `aa79cf9`, **antes** de qualquer teste de escala ser computado — ordem verificável no histórico. Registrado em `pre-registro.md` §5.2.

Substituição: **Fligner-Killeen** mais **IC 95% bootstrap percentílico da razão de IQRs**, 10.000 reamostragens, seed `20260909`. Critério: sustentada se Fligner rejeitar **e** o IC excluir 1,0.

Ressalvas registradas: o bootstrap **não** se ancora em Hoefler e Belli, que o exclui do escopo — justificativa vem de Efron e Tibshirani, ainda a acrescentar ao fichamento. E o desvio é **mais fraco que pré-registro limpo**, porque foi especificado após observar as descritivas; a monografia deve declarar isso, inclusive que a direção esperada já era conhecida.

### Resultado: nenhuma H3.x sustentada em N=20

| Comparação | Fligner-Killeen | razão de IQR | IC 95% bootstrap | Veredito |
|---|---|---|---|---|
| D0 vs D1 | p = 0,353 | 0,654 | [0,199 – 2,340] | não sustentada |
| D1 vs D2 | p = 0,586 | **1,335** | [0,431 – 3,918] | não sustentada |
| D2 vs D3 | p = 0,055 | 0,484 | [0,194 – 1,452] | não sustentada |
| **D0 vs D3** | **p = 0,034, rejeita** | 0,422 | [0,158 – 1,496] | **não sustentada** (IC inclui 1,0) |

Global nos quatro: p = 0,159, não rejeita.

O caso D0 vs D3 é instrutivo: o Fligner **rejeita**, mas o bootstrap inclui 1,0, e o critério é conjuntivo. Um critério disjuntivo daria outro resultado — mas o critério escrito é o que vale.

### Diagnóstico de poder e projeção

Razão de dispersões é estatística faminta de dados: os ICs abrangem um fator de dez, e `[0,199 – 2,340]` não distingue "metade da dispersão" de "o dobro".

Projetando pela contração em ~1/√N, de 20 para 50:

- **D0 vs D3** iria de `[0,16 – 1,50]` para algo como `[0,21 – 0,85]` — **excluiria 1,0**.
- **D0 vs D1** iria para `[0,40 – 1,07]` — marginal, provavelmente inconclusivo.

**Expectativa registrada antes de rodar N=50: o efeito cumulativo deve se estabelecer; a atribuição passo a passo provavelmente não.** Consequência do desenho, a constar como limitação.

### Por que D4 dissolve o problema de poder

Se D4 produzir **hashes idênticos**, a dispersão não é "menor" — é **exatamente zero**. Resultado categórico, como H1, sem necessidade de teste, e vale mais que qualquer IC de razão de IQR alcançável com 50 amostras. **D4 é o experimento decisivo do trabalho, não mais um degrau entre outros.**

### Item aberto: a anomalia de D2

**D2 tem mais dispersão que D1** — razão de IQR 1,335 — e persistiu de N=10 para N=20. Fisicamente estranho: D2 remove uma fonte em relação a D1. Candidatos: ruído de amostragem, o mais provável dado o IC `[0,431 – 3,918]`; ou algo não compreendido no escalonador. **Se sobreviver a N=50, deixa de ser ruído e exige explicação** — e seria achado por si.

## 2026-09-21 — Duas auditorias: toolchain Slang e mapeamento de D4

### Slang: metadados verificados e duas correções a afirmações minhas

Detalhamento em `../pivo-reprodutibilidade-3dgs/bibliografia/verificacao-vulkan-rdna4.md` §12.

- **Tag `v2026.2.1`**, asset `slang-2026.2.1-linux-x86_64.tar.gz`, 70.742.686 bytes. Binário autocontido; **não exige Vulkan SDK** — o backend SPIR-V é interno, `-emit-spirv-directly` é o default. Licença Apache-2.0 WITH LLVM-exception.
- **Não existe em apt.** ⚠️ E o pacote apt chamado `slang` é a **S-Lang**, biblioteca de terminal sem relação — conflito atestado pelo próprio `docs/building.md` do Slang.
- A release mais recente é `v2026.18`, ~30 releases à frente, e a ABI **não é estável**. **Pinar `2026.2.1`**, que é a versão com que o VkSplat foi testado.
- **Correção 1:** eu afirmei que `-fp-mode fast` "autoriza reassociação" de ponto flutuante. **A documentação oficial não diz isso** — diz apenas *"may change results"* e *"prefer the fastest version of special functions"*. Reassociação é hipótese plausível, não fato documentado. Resolve-se com experimento próprio: compilar com `fast` e com `precise`, e comparar o SPIR-V procurando `FPFastMathMode` e ausência de `NoContraction`. Barato, e daria um parágrafo forte.
- **Correção 2, mais séria:** o `slangc` tem `-denorm-mode-fp32` com **default `any`**, documentado como *"implementation defined"*, e o `compile_shaders.py` **não a fixa**. É fonte de divergência numérica **não controlada** que não estava no protocolo. Fixar ou declarar como limitação, antes de D4.

### D4: ponto fixo isolado **não** entrega bit-identidade — mas o desenho cumulativo salva

Achado central da auditoria de mapeamento. Duas razões:

1. O escalonador sorteia entre implementações, e elas agrupam os termos de forma diferente **antes** do atômico, em somas parciais **em float**.
2. Dentro de cada implementação há pré-redução em float: `WaveActiveSum` no `per_pixel`, `reduce_splats` em memória compartilhada no `tensor`. **A exceção é o `per_splat`**, onde a pré-redução é acumulação sequencial em registrador, com ordem fixada pelo laço, logo determinística.

**Como D2 já fixa a implementação em `PerSplat` e D4 é cumulativo sobre D2, converter apenas o `per_splat` fecha a bit-identidade.** O desenho cumulativo da escada, adotado por outra razão, resolveu este problema por acidente — mas a **dependência D2 → D4 precisa ser declarada no texto**: o patch cobre uma de três variantes, e isso só é válido porque D2 é cumulativo.

### O que destrava a medição hoje, sem depender da Slang

**O binding Python já expõe os três buffers de gradiente como numpy** — `module.v_xy_vs`, `module.v_inv_cov_vs_opacity`, `module.v_rgb` — além de `module.tiles_touched` e `module.radii`. Portanto a magnitude dos gradientes e a distribuição de K (tiles por gaussiana) são **mensuráveis sem uma linha de código novo**. A hipótese de que isso exigiria mudança em C++ estava errada, e para melhor: a medição pode começar antes de a toolchain chegar.

### Fatos que o plano de D4 herdou

- **Zero mudanças em C++.** Os buffers são `RWByteAddressBuffer` nos produtores e `Buffer<float>` no C++; como `sizeof(float) == sizeof(int32_t)`, os mesmos bytes viram inteiro sem realocar. E o zeramento por passo é `vkCmdFillBuffer(..., 0)` — **zero bytes é ao mesmo tempo `0.0f` e `int32_t(0)`**.
- **Não existe atômico de 64 bits em nenhum lugar do repositório.** `USE_EMULATED_INT64` não tem relação com atômicos e nunca é acionada. A escala tem de caber em `int32`.
- **Não há precedente de `InterlockedAdd` inteiro sobre `RWByteAddressBuffer`** em nenhum `.slang` nem nos `.spv` versionados. Se o `slangc` não emitir SPIR-V válido para isso, D4 exige outro desenho. **Principal risco técnico em aberto**, verificável em minutos com a toolchain em disco.
- **Segundo consumidor que eu não conhecia:** `default.slang`, fase `UpdateState`, lê `v_xy_vs` e alimenta um **teste de limiar** contra `grow_grad2d = 0.0002`. Adam é invariante a escala global; **este consumidor não é**. Logo o erro de quantização do ponto fixo **propaga direto para a decisão de duplicar/dividir gaussianas** — e o número de gaussianas é um dos observáveis do trabalho. É o candidato mais provável a fazer D4 trocar determinismo por qualidade.
- **Não há limite dedicado de tiles por gaussiana**: `K ≤ grid_width × grid_height`, com *clamp* só contra o grid.

Plano completo em `../pivo-reprodutibilidade-3dgs/pre-registro.md` §10.

## 2026-09-21 — Auditoria dos dados em disco: **D3 não é uma série homogênea**

Auditoria de evidência, não de leitura: contagem de execuções, conferência de hashes, reexecução de `analise_dispersao.py` e inspeção de `env.json`/`origem.txt` de todas as 80 execuções.

### O que confere exatamente

- **N=20 em cada um de D0, D1, D2, D3.** 20 diretórios `run*` e 60 linhas de manifesto por degrau.
- **80 hashes de `splat.ply`, 80 distintos** — 20/20 em cada degrau, e 80 distintos no agregado. **H1 reconfirmada por evidência.**
- Commit uniforme dentro de cada degrau: D0 `3a5c0d97a6`, D1 `4cb921a82f`, D2 `b395759efa`, D3 `d222c47182`.
- Descritivas de D0 reproduzidas dígito a dígito: mediana 27,3614; IQR 0,0507; amplitude 0,1905; **H2 = 27/190 = 14,2%**. IQRs de D1 0,0331, D2 0,0442, D3 0,0214 — todos batem com a tabela da entrada de 09-08/09.
- Dispositivo idêntico nas 80: `AMD Radeon RX 9070 XT (RADV GFX1201)`, `has_float32_atomic_add: true`, `subgroup_size: 64`. Nenhuma execução caiu em `llvmpipe`; nenhuma caiu em emulação de atômico.

### O que **não** confere — achado principal desta auditoria

**O kernel não é constante em D3.** Por `env.json`:

| Degrau | `7.0.0-30-generic` | `7.0.0-31-generic` |
|---|---|---|
| D0 | 20 | 0 |
| D1 | 20 | 0 |
| D2 | 20 | 0 |
| **D3** | **10** (`run000`–`run009`) | **10** (`run010`–`run019`) |

A divisão coincide exatamente com uma lacuna de 11 dias, por `origem.txt`:

- D0, D1, D2: os dois blocos de 10 correram em sequência contínua entre `20260908_225237` e `20260910_042513`.
- **D3: bloco 1 em `20260909_165623`–`20260909_193002`; bloco 2 em `20260920_224213`–`20260921_011547`.**

O intercalamento declarado (D0→D1→D2→D3, depois repetir) **de fato ocorreu** — mas o segundo bloco de D3 ficou pendente e foi completado 11 dias depois, atravessando uma atualização de kernel. Isso é o commit `b876397` ("D3 faltante"). **A justificativa escrita para o intercalamento era "evitar confundir o efeito do degrau com fatores que variem no tempo"; para D3, e só para D3, essa proteção não valeu.**

### Por que isto exige escrutínio e não nota de rodapé

D3 é o degrau cujos números **mais favorecem a tese**: menor IQR (0,0214), único com **0/190** pares ≥ 0,10 dB, e o único cujo Fligner-Killeen rejeita contra D0 (p = 0,034). É precisamente o achado que a disciplina de método manda examinar com rigor **maior**.

Separando D3 pelos dois blocos (PSNR, N=10 cada — **análise post-hoc, exploratória, não pré-registrada**):

| Bloco | kernel | mediana | IQR | amplitude |
|---|---|---|---|---|
| `run000`–`run009` (09-09) | `-30` | 27,3900 | 0,0131 | 0,0526 |
| `run010`–`run019` (09-20/21) | `-31` | 27,3867 | 0,0255 | 0,0813 |

Leitura honesta dos dois sentidos:

- **Tranquilizador quanto a posição:** as medianas diferem 0,0033 dB, duas ordens abaixo do limiar de 0,10 dB. Não há deslocamento atribuível ao kernel.
- **Não conclusivo quanto a escala, e não pode ser usado nos dois sentidos:** o IQR quase dobra entre blocos, mas com N=10 por bloco isso é indistinguível de ruído — com N=20 o IC bootstrap da razão de IQRs já cobria um fator de dez. **Não se pode afirmar que o kernel alterou a dispersão, nem que não alterou.**
- **A consequência desconfortável:** se a heterogeneidade infla o IQR agregado de D3, então restringir D3 ao bloco homogêneo (IQR 0,0131) reforçaria H3.4. **Fazer esse recorte depois de ver os dados seria seleção de subconjunto favorável.** Fica proibido sem desvio declarado e datado, e a razão de ser proibido é justamente ele favorecer a tese.

### Lacuna de instrumentação que este achado expõe

**O `env.json` não registra a versão do Mesa/RADV** — só o `deviceName`. Em um trabalho sobre reprodutibilidade numérica, o driver é o compilador de SPIR-V para ISA, e portanto é variável de primeira ordem. Como o kernel mudou, é plausível que pacotes de userspace tenham mudado junto, **mas não há dado em disco para decidir, e não se vai afirmar causa sem a saída literal.** Se a máquina Ubuntu ainda tiver o histórico do gerenciador de pacotes, a versão do Mesa em 09-09 e em 09-20 é recuperável a posteriori; caso contrário, entra como limitação declarada. Acrescentar Mesa, versão do RADV e `vulkaninfo` resumido ao `env.json` antes de qualquer série nova.

### Terceira divergência: o ciclo N=30

O caderno registrava, em "Em andamento", um **ciclo N=30 nos quatro degraus, ~11h de máquina**. **Não existe nenhum diretório `run020` ou superior em nenhum degrau do repositório.** O que de fato entrou entre 09-10 e 09-21 foi o completamento de D3 até N=20. Se o ciclo N=30 rodou na máquina Ubuntu e não foi sincronizado, é questão de transferência; se não rodou, a linha era projeção e não estado. **Não há evidência em disco para distinguir, e a linha foi corrigida para refletir só o que se pode verificar.**

### Encaminhamento, sem alterar protocolo

Nada aqui muda o pré-registro. As opções, a decidir com o aluno e a registrar como desvio datado se alguma for adotada:

1. **Declarar como limitação** e manter D3 com N=20 heterogêneo. Conservador, e defensável.
2. **Reexecutar D3 inteiro** sob ambiente único, junto com o ciclo de ampliação de N. Custo ~4,7 h de máquina para 20 execuções a 942 s.
3. Tratar o bloco como fator explícito na análise. Aumenta complexidade e continua sem poder com N=10.

A opção 2 é a única que restaura a homogeneidade sem seleção post-hoc, e ela se paga se o ciclo de ampliação de N for rodar de todo modo.

## 2026-09-21 — Instrumentação de ambiente acrescentada ao orquestrador

Resposta à lacuna apontada na auditoria acima. `run_degree.sh` passa a gravar `ambiente.json` — versão de kernel e de oito pacotes de Mesa/Vulkan/libdrm via `dpkg-query`, mais `vulkaninfo` e `glxinfo` com *fallback* — uma vez por série e uma vez por execução, ao lado do `env.json`. Também ecoa kernel e `mesa-vulkan-drivers` no terminal a cada execução, para heterogeneidade aparecer na hora e não numa auditoria 11 dias depois.

**Onde a instrumentação foi posta, e por que não no `tcc_runner.py`.** O `tcc_runner.py` é quem grava o `env.json`, e seria o lugar óbvio — mas ele vive no fork, dentro dos commits e tags dos degraus. Editá-lo teria dois efeitos inaceitáveis: sujaria a árvore do fork, fazendo o próprio `run_degree.sh` abortar na checagem de §9; e alteraria os SHAs de `pre-registro.md` §3.1, que identificam os degraus. O orquestrador é camada **acima** da escada e não pertence ao estado de código de nenhum degrau — é o mesmo argumento do desvio declarado em 2026-09-02. **Nenhum arquivo do fork foi tocado, e nenhum SHA de degrau muda.**

**Natureza da mudança:** puramente observacional. Não altera configuração, seed, dataset, número de passos nem qualquer parâmetro do treino; apenas registra o que já estava lá e não era anotado. Não é desvio de protocolo, é acréscimo de registro — mas fica datado aqui para que séries antigas e novas sejam distinguíveis: **execuções até `D3/run019` não têm `ambiente.json`; da próxima série em diante, têm.**

**Verificação parcial, e o que falta.** `bash -n` passa e o JSON gerado valida em `json.tool`. Mas o teste foi feito **no Mac**, onde `dpkg-query`, `vulkaninfo` e `glxinfo` não existem — exercitou os *fallbacks*, não o caminho real. E expôs um detalhe: `date -Is` é GNU, não BSD, então `snapshot_em` saiu vazio no Mac. Na Ubuntu funciona, e o script já usava `date -Is` antes desta mudança. **Ainda assim, o caminho real só estará verificado quando o primeiro `ambiente.json` da Ubuntu for lido — conferir isso antes de confiar na série da noite de 2026-09-21.**

### Âncora retroativa recuperada do inventário

`experimentos/00-inventario/saidas/inventario-fabio-desktop-20260825T222551Z.md` registra, em **2026-08-25**, via `dpkg -l`:

- `mesa-vulkan-drivers:amd64` **25.2.8-0ubuntu0.24.04.2** — é o pacote que fornece o RADV
- `libgl1-mesa-dri`, `libegl-mesa0`, `libglx-mesa0`, `mesa-libgallium`: todos `25.2.8-0ubuntu0.24.04.2`
- `libvulkan1:amd64` `1.3.275.0-1build1`; `libdrm-amdgpu1` `2.4.125-1ubuntu0.1~24.04.2`
- kernel `7.0.0-30-generic #30~24.04.1-Ubuntu ... Fri Aug 7 13:27:52 UTC`

Note que o bloco de `vulkaninfo` desse inventário saiu **vazio** — motivo pelo qual `dpkg` é a fonte primária da versão no novo snapshot, e o `vulkaninfo` só complemento.

Isso dá um ponto de ancoragem **antes** das séries, não entre os blocos de D3. **A versão do Mesa em 2026-09-09 e em 2026-09-20 continua desconhecida** e só é recuperável pelo histórico do gerenciador de pacotes na máquina Ubuntu.

### Premissa do aluno que a evidência refuta

O aluno relatou não ter atualizado nada no sistema desde o início do TCC. **O `env.json` mostra kernel `7.0.0-30-generic` em 09-09 e `7.0.0-31-generic` em 09-20/21.** Um kernel HWE novo não aparece sem instalação de pacote, e não passa a ser usado sem reinício. Portanto **houve instalação de pacote e reinício nesse intervalo**, independentemente de ter sido deliberada — `unattended-upgrades` é ativo por padrão no Ubuntu para o *pocket* de segurança, e o cenário consistente é instalação automática em algum momento seguida de reinício antes de 09-20.

Consequência de método: **a premissa "nada mudou, logo o Mesa é o mesmo" não se sustenta**, porque ela já é falsa para o kernel. Não se está afirmando que o Mesa mudou — está-se registrando que a inferência não é válida e que a questão é empírica. Resolve-se lendo `/var/log/dpkg.log*` e `/var/log/apt/history.log*` na Ubuntu, e **isso deve ser feito antes de a série da noite começar**, porque é de graça e porque o log rotaciona.

## 2026-09-21 — Agente de busca de originalidade criado

Criado `.optimus/agent/originalidade-3dgs.md`, agente dedicado a fechar a **lacuna 2** do fichamento (`pivo-reprodutibilidade-3dgs/bibliografia/fichamento.md`), que hoje impede qualquer alegação de novidade.

Desenho deliberadamente **adversarial**: a tarefa é procurar o trabalho que torne o TCC redundante, não confirmar que ele é inédito. Achado que ameace a originalidade vai ao topo do relatório. A reivindicação foi decomposta em três partes testáveis separadamente — quantificação, isolamento a seed fixa, atribuição por ablação e intervenção — porque elas têm forças de evidência diferentes e podem cair independentemente.

Cobertura exigida: IEEE Xplore, ACM DL, Eurographics Diglib, OpenReview, Semantic Scholar, DBLP, HAL e Zenodo; termos ampliados incluindo `bitwise reproducibility` e `run-to-run variance`; e issues/PRs dos cinco repositórios, que a lacuna 2 identifica como a fonte provavelmente mais produtiva. Itens nominais a resolver: survey `Advanced3DGS`, leitura integral de FreeTimeGS++ (arXiv:2605.03337) e de NerfBaselines (arXiv:2406.17345).

**Restrições dadas ao agente:** não escreve nem edita arquivo nenhum do repositório, não commita, não altera o pré-registro. Entrega relatório; a incorporação ao fichamento é decisão do aluno. E é obrigado a entregar **tabela de cobertura com as queries literais, contagens e datas de acesso** — sem ela, "nada encontrado" não é afirmável, apenas "não encontrado por esta busca".

**Disparado em 2026-09-21.** A primeira execução **travou** após ~5 minutos e foi abortada; relançada em seguida. Ver a entrada "Primeira execução do agente travou" abaixo, que registra o achado parcial obtido antes da parada — ele é relevante por si.

## 2026-09-21 — Histórico de pacotes lido: **o Mesa não mudou, e o dano é menor do que parecia**

Saída literal de `/var/log/dpkg.log*`, `/var/log/apt/history.log*` e `journalctl --list-boots` na máquina Ubuntu, colhida antes de disparar a série da noite. Fecha a pendência aberta na auditoria de hoje.

### Achado principal: o RADV é o mesmo nas 80 execuções

**Na janela 2026-09-09 a 2026-09-21, o `dpkg.log` não registra nenhuma instalação ou atualização de pacote Mesa, Vulkan ou libdrm.** A lista completa das 79 transações na janela contém kernel, gnupg, sssd, openssh-client, spice-vdagent, librabbitmq4, linux-libc-dev, linux-tools-common — e, em 2026-09-21 06:36, gstreamer, polkit, python3.12, perl, libinput, libc6, libsoup, libaom3, libsqlite3, bubblewrap, wireless-regdb. **Nenhum `mesa-*`, nenhum `libvulkan*`, nenhum `libdrm*`, nenhum `libgl*`.**

Combinado com a âncora do inventário de 2026-08-25, que registra `mesa-vulkan-drivers 25.2.8-0ubuntu0.24.04.2`: **o compilador de SPIR-V para ISA foi o mesmo nas 80 execuções.** A preocupação central levantada hoje — de que o driver pudesse ter mudado no meio de D3 — **está descartada por evidência, não por suposição.**

### A cronologia exata, agora estabelecida

- `2026-09-09 11:28:52` — `install linux-image-7.0.0-31-generic`, `upgrade linux-image-generic-hwe-24.04 7.0.0-30.30 → 7.0.0-31.31`. Por `apt/history.log`, o autor destas transações é `/usr/bin/unattended-upgrade`.
- O kernel novo **não passou a valer na hora**: por `journalctl --list-boots`, o boot `-1` durou de `2026-09-08 21:24:59` a `2026-09-10 07:47:12`. **Setenta das oitenta execuções correram nesse único boot**, sob kernel `-30` — D0, D1 e D2 completos, mais D3 `run000`–`run009`.
- O boot `0` começou em `2026-09-20 22:24:31`, já com `-31`. D3 `run010` começou às `22:42`. **As dez execuções finais de D3 são as únicas em ambiente diferente**, e a diferença é o kernel mais pacotes sem relação com o pipeline gráfico.

Note a coincidência que enganaria qualquer um: a instalação do kernel às `11:28:52` foi **três minutos** antes de D1 `run000` começar, às `11:35:52`. Se a atribuição de kernel tivesse sido feita pela data de instalação do pacote em vez do `uname -r` gravado no `env.json`, a conclusão seria oposta e errada.

### O dano é localizado, e não atinge as hipóteses sustentadas

Vale conferir com desconfiança, porque é conclusão conveniente:

- **D0 é 20/20 homogêneo:** mesmo boot, mesmo kernel, mesmo Mesa. **H2, a afirmação metodológica central do trabalho, repousa sobre dados não afetados.** Os 14,2% de pares com |ΔPSNR| ≥ 0,10 dB estão limpos.
- **H1 é imune por construção.** Execuções dentro do mesmo boot já produzem hashes distintos; heterogeneidade de ambiente não pode explicar 80/80.
- **A heterogeneidade está confinada a D3**, que entra nas H3.x — e **nenhuma H3.x se sustentou de todo modo**. O defeito de dados afeta exatamente a parte do trabalho já declarada como não estabelecida por falta de poder.

Continua valendo a proibição: **não restringir D3 ao bloco homogêneo**, porque daria IQR 0,0131 em vez de 0,0214 e reforçaria H3.4 por seleção post-hoc.

### Variável nova, que só apareceu por ler o log até o fim

Em `2026-09-21 06:36`, portanto **depois** de D3 `run019` terminar (~01:31) e **antes** da série da noite, `unattended-upgrade` atualizou `libc6` 2.39-0ubuntu8.8 → 8.9 e `python3.12` 3.12.3-1ubuntu0.15 → 0.17, entre outros.

Por que não é irrelevante: `libc6` carrega a **libm**, e as métricas PSNR/SSIM/LPIPS são computadas em PyTorch de CPU. Mudança em função transcendental de libm alteraria resultados no último bit. **É hipótese plausível, não fato verificado** — não se está afirmando que muda nada. Afirma-se que é variável não controlada, não registrada, e que a série da noite correrá sob libc e Python diferentes das 80 anteriores. Agravante: o `env.json` grava `python: 3.12.3 (main, Jun 19 2026, ...)`, a versão **upstream**, que não distingue revisão Ubuntu `0.15` de `0.17`.

Consequência: `snapshot_ambiente` em `run_degree.sh` passou a registrar também `libc6`, `python3.12`, `libpython3.12t64` e o **`boot_id`** — este último para que separação por reinício apareça no dado, em vez de ter de ser reconstruída de timestamps 11 dias depois.

### Recomendação registrada: congelar o ambiente

`unattended-upgrade` alterou o ambiente **duas vezes dentro da janela experimental** — `2026-09-09 11:28` e `2026-09-21 06:36`. Num trabalho cujo objeto é reprodutibilidade, ambiente que se altera sozinho entre séries é defeito de método, e a evidência agora é literal.

Sugerido ao aluno mascarar as unidades de atualização automática até o depósito, e registrar a data, para que séries posteriores sejam declaradamente de ambiente congelado. **Decisão do aluno; não executado por iniciativa própria.**

## 2026-09-21 — **Ambiente congelado.** Marco de protocolo

O aluno executou, e a saída literal confirma:

```
sudo systemctl mask unattended-upgrades.service apt-daily.timer apt-daily-upgrade.timer
Created symlink /etc/systemd/system/unattended-upgrades.service → /dev/null.
Created symlink /etc/systemd/system/apt-daily.timer → /dev/null.
Created symlink /etc/systemd/system/apt-daily-upgrade.timer → /dev/null.

systemctl is-enabled unattended-upgrades.service apt-daily-upgrade.timer
masked
masked
```

**Data do congelamento: 2026-09-21.** É um marco que divide o experimento em duas eras, e o texto deve declará-lo:

- **Antes:** as 80 execuções de D0–D3 correram sob ambiente que se alterou sozinho **duas vezes** (`2026-09-09 11:28` e `2026-09-21 06:36`, ambas por `/usr/bin/unattended-upgrade`). As consequências efetivas estão delimitadas: kernel heterogêneo em D3, e `libc6`/`python3.12` distintos para séries a partir de hoje. **O Mesa/RADV nunca mudou**, o que é o que mais importaria.
- **Depois:** ambiente declaradamente congelado, e a afirmação "execuções nominalmente idênticas" passa a incluir o ambiente de userspace, não apenas cena, seed, commit e máquina.

**Pendência de baixo custo:** reverter o mascaramento após o depósito (`systemctl unmask`), para a máquina não ficar sem correções de segurança indefinidamente. Não é problema de pesquisa, é higiene — mas fica anotado porque é o tipo de coisa que se esquece.

**Limitação a declarar no texto:** congelar o ambiente **hoje** não retroage. As 80 execuções já medidas permanecem como estão, e a heterogeneidade de D3 permanece um fato a declarar, não a corrigir.

## 2026-09-21 — Primeira execução do agente de originalidade travou, e o achado parcial importa

A primeira execução parou após cerca de cinco minutos e ficou dez minutos sem progresso em dois comandos `grep` locais, que deveriam levar menos de um segundo. Estado inconsistente: a sessão reportava `idle` enquanto duas chamadas de ferramenta seguiam marcadas como `running`. **A causa não foi determinada e não se vai afirmar uma** — o registro fica aqui como fato operacional. Contexto que pode ou não ser relevante: imediatamente antes, o agente havia pedido liberação de proxy para `arxiv.org`, o grant foi concedido, usado com sucesso, e expirou. A relançada foi instruída a não usar esse mecanismo e a não disparar comandos em paralelo.

### Achado parcial, verificado antes da parada — e é um sinal de alerta

O agente baixou as duas maiores ameaças à originalidade e contou ocorrências. Resultado, por contagem sobre o texto extraído do HTML do arXiv:

- **FreeTimeGS++**, título confirmado: *"FreeTimeGS++: Secrets of Dynamic Gaussian Splatting and Their Principles"*. Existem **três versões** (v1, v2, v3); v3 é a corrente.
- A subseção **"Secret 5" sobreviveu até v3** — 2 ocorrências em v1, 2 em v2, 3 em v3.
- **A expressão `run-to-run` aparece 3 vezes em v1, 3 em v2 e 10 em v3.** A versão atual **expandiu** a discussão de variação entre execuções.
- **NerfBaselines** (arXiv:2406.17345) tem v1 e v2; v3 não existe (HTTP 404).

**Por que o salto de 3 para 10 merece atenção imediata, e não celebração:** o levantamento de 2026-08-26 avaliou a ameaça de FreeTimeGS++ com base no HTML principal, sem comparar versões. Se v3 aprofundou a análise de variação entre execuções, os autores podem ter avançado para o território que o TCC reivindica — em particular a **reivindicação 2** (ninguém isola o não-determinismo a seed fixa). A questão decisiva, agora explicitamente na tarefa do agente: **em algum ponto eles fixam a seed e ainda observam variação, e atribuem a causa a atômicos ou a ordem de execução em GPU?** Se a resposta for sim, a reivindicação 2 cai.

Isto é exatamente o caso em que a disciplina manda escrutínio maior, porque a leitura confortável — "é 4DGS dinâmico, é outro objeto" — é a que interessa ao trabalho. **Nada sobre a distinção em quatro dimensões pode ser afirmado até que os trechos literais de v3 sejam lidos.**

Arquivos em `/tmp/orig3dgs/` (fora do repositório, não versionados): HTML e texto extraído das cinco versões, mais o conversor. Se a máquina for reiniciada, `/tmp` é limpo e o download precisa ser refeito — **se o resultado for usado no texto, transcrever os trechos literais para o fichamento antes disso.**

## 2026-09-21 — Busca de originalidade concluída: **a reivindicação de quantificação caiu**

Relatório da segunda execução do agente `originalidade-3dgs`. **Verifiquei de forma independente os dois achados decisivos** nos arquivos em `/tmp/orig3dgs/`, porque obrigam a reescrever o `PLANO.md` e porque um relatório que derruba uma reivindicação central não deve ser aceito sem conferência. Ambos confirmados; um erro de contagem do agente encontrado e corrigido.

### Achado 1 — NerfBaselines v2: novo, grave, e ninguém no projeto tinha lido

**KULHANEK, Jonas; SATTLER, Torsten. *NerfBaselines: Consistent and Reproducible Evaluation of Novel View Synthesis Methods*. arXiv:2406.17345.** v1 de 2024-06-25; **v2 de 2025-10-29**, corrente. Venue "NeurIPS 2025 D&B" consta **apenas do comentário dos autores** no arXiv, sem registro independente e sem DOI — `nao verificado` para efeito ABNT.

Conferido por mim no HTML bruto, linha 240 do texto extraído da v2:

> *"We also report the standard deviation computed over four independent trainings of each method."*

Valores na Tabela 2, para o conjunto do TCC (Mip-NeRF 360): 3DGS `27,43 ± 0,02` (protocolo P1) e `27,68 ± 0,03` (P2); gsplat `27,41 ± 0,02` e `27,68 ± 0,02`.

**A mudança entre versões, que é o ponto:**

| | v1 (2024-06-25) | v2 (2025-10-29) |
|---|---|---|
| `standard deviation` | **0** ocorrências | **2** ocorrências |
| `seed` (qualquer forma) | **1** — *"For all methods, we fix random seeds to match the official implementations."* | **0** |

Contagens minhas, sobre o HTML bruto, não sobre o texto extraído. **A v2 acrescentou dispersão entre execuções e apagou a declaração de seed fixa.** O protocolo de seed da v2 é, portanto, **indeterminado no artigo**.

**Consequência:** se aquelas quatro execuções herdaram o comportamento declarado na v1, então NerfBaselines já mediu dispersão entre execuções **a seed fixa, em 3DGS estático, no Mip-NeRF 360**, e publicou. Isso derrubaria a reivindicação de isolamento a seed fixa por inteiro. **O artigo não permite decidir.**

### Achado 2 — FreeTimeGS++ v3: as quatro distinções se sustentam, mas duas estão mais estreitas

**LEE, Lucas Yunkyu; KIM, Soonho; KIM, Youngwook; KIM, Sangmin; PARK, Jaesik. *FreeTimeGS++: Secrets of Dynamic Gaussian Splatting and Their Principles*. arXiv:2605.03337.** v1 2026-05-05, v2 2026-05-29, **v3 2026-07-01**. Preprint, sem venue e sem DOI.

- **Objeto (4DGS dinâmico):** sustenta-se.
- **Causa atribuída:** sustenta-se **com folga**. Contagem do agente de `atomic|nondetermin|determinis|floating.point|float32|associat|bitwise` nas três versões: v1=0, v2=0, v3=1, e essa única é falso positivo (*"temporal scale associated with duration"*). A atribuição deles é literalmente *"small stochastic differences"* — não investigadas.
- **Intervenção fotométrica:** sustenta-se. *"affine color correction (CC) module which acts as a training-time stabilizer that absorbs photometric variation."*
- **Seed fixa × variável: sustenta-se, mas ESTREITADA.** Eles variam a seed (`run r` usa `seed S+r`, base 0 — o agente teve de recuperar do HTML porque o `strip` come as fórmulas). **Mas fixam a inicialização e declaram isolar uma fonte**, o que conferi literalmente: *"we fix the initialization and repeat optimization under the same protocol."* Logo o contraste real é "seed fixa" × "seed variável **com inicialização fixa**", não "sem nenhum isolamento". Escrever a versão forte expõe o Cap. 1 a uma objeção de dez segundos.

**A deriva entre versões é o risco vivo.** `run-to-run` aparece 3 vezes em v1, 3 em v2 e **10** em v3. O enunciado do "Secret 5" mudou de registro: v1 dizia *"Flexibility introduces instability, making reconstruction poorly repeatable"* — afirmação sobre o objeto; v3 diz *"Single-run scores can hide run-to-run variation"* — afirmação sobre a **prática de reporte**, que é a tese metodológica deste TCC aplicada a 4DGS. N deles subiu de 6 para 10 execuções. **Monitorar este arXiv ID até o depósito:** uma v4 que fixe seed ou investigue causa numérica custaria duas reivindicações de uma vez.

### Erro do agente, encontrado na conferência — e é erro de método, não de aritmética

O agente reportou **9** ocorrências de `run-to-run` em v3 e, ao notar divergência da contagem anterior (10), **ofereceu uma explicação elaborada** — que a contagem de 10 "provavelmente contou também a legenda da Figura 5 com capitalização diferente ou uma ocorrência em `<math>`".

Conferi: são **10**, por `grep -o` e por `grep -c`. A contagem do agente estava errada e a explicação era racionalização de um erro próprio.

É pequeno no conteúdo e grande no método: é **exatamente** o padrão que este projeto já pagou caro — diagnóstico emitido com confiança acima da evidência, em vez de reverificação. Registrado aqui porque o mesmo agente será usado de novo e porque a lição vale para mim também.

### Defesa técnica que o relatório menciona mas não explora, e que é a melhor disponível

NerfBaselines agrega **no nível de dataset**: linha 239, *"we show the PSNR averaged over all scenes of the Mip-NeRF 360 dataset"*. Portanto o `± 0,02` é o desvio da **média sobre nove cenas**, não de uma cena.

**Inferência minha, a verificar antes de usar no texto, e não dado deles:** se as cenas fossem independentes, o desvio por cena seria da ordem de `0,02 × √9 = 0,06 dB` — mesma ordem do IQR de D0 medido aqui (0,0507 dB). Ou seja, a medição deles **não contradiz** a deste trabalho, e plausivelmente a corrobora; e a agregação por dataset **comprime** a dispersão que o TCC mede por cena. Isto é defesa legítima e é também argumento metodológico próprio: reportar σ de média de cenas esconde a dispersão por cena. **Não escrever como se fosse número deles.**

### O que muda no PLANO, e o que não muda

**Cai:** a afirmação de que o fenômeno "nunca foi quantificado publicamente". Dois trabalhos quantificam com estatística declarada, mais o VkSplat com IC de 90%. Somados, a novidade do aparato estatístico é **fina**.

**Fica em suspenso:** o isolamento a seed fixa, até o protocolo de seed da v2 do NerfBaselines ser resolvido.

**Sobrevive, e com as contagens a favor:** **mecanismo, ablação e intervenção.** Zero menções a atômicos, não-determinismo ou associatividade nos dois trabalhos ameaçadores. Nenhuma proposta de treino determinístico encontrada. `harry7557558/vksplat` reconfirmado em **0 issues e 0 PRs** (`total_count: 0` na API do GitHub).

**Consequência de escopo, e ela reforça decisão já tomada:** o centro de gravidade do trabalho deve se deslocar explicitamente para **D4 e a escada de ablação**. É onde as buscas dão zero, é onde há código autoral, e é o que nenhum dos dois trabalhos toca. A §2.1.5 do `PLANO.md` já apontava o eixo 2 como contribuição principal; agora há evidência externa para isso.

### Correção a um dado que o PLANO já registra, a verificar

`PLANO.md` §2.1.3 atribui ao relato de 45 execuções da issue #89 hiperparâmetros alterados *"(`percent_dense=1e-5`)"*. O agente afirma que **o corpo da issue não contém `1e-5`**, e que o que há é menção a alteração de `position_lr`, `scaling_lr`, `lambda_dssim` e `percent_dense`, com discussão de `0,01` contra `0,1`. **Não conferi de forma independente** — fica como pendência. Enquanto não resolvido, remover o número do texto e dizer apenas "hiperparâmetros alterados, incluindo `percent_dense`".

O agente registra também que o autor da #89 **atribuiu a causa errado** — a *split* da densificação e à escolha aleatória de câmera, nada de atômicos — e que declarava seed fixa, com PSNR de 24,23 a 28,06 em 45 execuções. Se confirmado, é argumento a favor do TCC: o fenômeno era conhecido e **mal atribuído**.

### A busca continua incompleta — a ressalva do §2.5 permanece obrigatória

Não consultados: **IEEE Xplore, ACM DL, Eurographics Diglib, OpenReview** (não tentados, por orçamento de contexto — não há evidência de inacessibilidade). **Semantic Scholar** deu `HTTP 429`. **DBLP** está atrás de muro anti-bot Anubis com prova de trabalho em JavaScript. Também pendentes: HAL/Zenodo para a lacuna 3; 8 dos 11 PRs com "deterministic" não revisados; reverificação das citações literais da issue #2996 e do PR #970, ambas de peso no Cap. 2; e o survey **`Advanced3DGS` não foi localizado nem refutado** — não se conseguiu confirmar que existe obra com esse nome.

**Nota operacional útil:** o agente tentou paralelizar com subagentes e falhou — subagentes rodam com `network deny` e não conseguem usar `webfetch`, embora a sessão principal consiga. Não repetir a tentativa.

### Duas referências a acrescentar ao fichamento

Conferido: `FreeTimeGS|NerfBaselines|2605.03337|2406.17345` dá **zero** ocorrências no `fichamento.md` atual. Ambas precisam entrar, e o agente sugere um eixo novo — "trabalhos que reportam dispersão" — que é o que a lacuna 2 de fato exige. Registrar na entrada do NerfBaselines a **diferença v1/v2 quanto à seed**, porque é o dado que decide a reivindicação.

### Ação de maior retorno, pendente de decisão do aluno

Perguntar a Jonáš Kulhánek, por issue no repositório do NerfBaselines ou por e-mail, **se as quatro execuções da Tabela 2 usaram seeds fixas ou variadas**. É uma pergunta de uma linha que decide a reivindicação central do trabalho. Alternativa sem contato: o NerfBaselines é código aberto — inspecionar se o *runner* semeia por execução.





## Estado em 2026-09-21 — ponto de entrada para sessão nova


> Esta é a seção a ler primeiro. O `CLAUDE.md` da raiz aponta para cá.

### Feito

- **Pré-registro estágio 1** commitado em `879dc8751e9c3d229506028600998840f24bb227`, cobrindo D0 a D3. **Desvio declarado** do teste estatístico em `aa79cf9`.
- **Escada de cinco degraus** implementada e travada em commits no fork `github.com/fabio-gabriel/vksplatTCC`, branch `tcc-base`, com tags `D0`–`D3`. SHAs em `pre-registro.md` §3.1.
- **80 execuções medidas:** N=20 em cada um de D0, D1, D2, D3. **Conferido por evidência em 2026-09-21** (contagem de diretórios, manifestos e reexecução da análise).
- **H1 confirmada de forma categórica: 80 execuções, 80 hashes distintos.** Sobrevive a D1, o que elimina a explicação mundana do embaralhamento não semeado. Reconferido em 2026-09-21.
- **H2 sustentada** sobre D0: 14,2% dos pares com |ΔPSNR| ≥ 0,10 dB, contra critério de 5%. Reconferido em 2026-09-21.
- **Custo do determinismo medido:** D3 é 14% mais lento que D2.
- Dados, manifestos de hash e logs versionados em `pivo-reprodutibilidade-3dgs/dados/<degrau>/`.
- **Plano completo de D4** em `pre-registro.md` §10, com o conjunto exato de mudanças.

### Em andamento

- **Ciclo N=30 nos quatro degraus: confirmado pelo aluno em 2026-09-21 como NÃO executado ainda.** Vai rodar na noite de 2026-09-21. A linha anterior deste caderno o registrava como "em andamento", o que era projeção e não estado — corrigido. **A máquina está hoje em kernel `7.0.0-31`, e isso condiciona o sequenciamento: ver abaixo.**

### Defeito de dados aberto — decidir antes de ampliar N

**D3 não é série homogênea:** `run000`–`run009` sob kernel `7.0.0-30-generic` (2026-09-09, boot `-1`), `run010`–`run019` sob `7.0.0-31-generic` (2026-09-20/21, boot `0`). D0, D1 e D2 são homogêneos em `-30` e **no mesmo boot**. Medianas dos dois blocos de D3 diferem só 0,0033 dB, mas o IQR quase dobra — indistinguível de ruído com N=10, e portanto **não afirmável em nenhum dos dois sentidos**. **Restringir D3 ao bloco homogêneo está proibido sem desvio declarado**, precisamente por ser o recorte favorável.

**Gravidade rebaixada em 2026-09-21, por evidência:** o `dpkg.log` mostra que **nenhum pacote Mesa/Vulkan/libdrm mudou** na janela — o RADV foi o mesmo nas 80 execuções. A diferença entre os blocos de D3 é **somente o kernel**. E o dano não atinge as hipóteses sustentadas: D0 é 20/20 homogêneo, logo **H2 está limpa**; H1 é imune por construção; a heterogeneidade está confinada a D3, que entra nas H3.x, nenhuma das quais se sustentou. Ver a entrada "Histórico de pacotes lido".

**Consequência para a série de ampliação, a decidir ANTES de disparar:** rodar `run020`–`run029` nos quatro degraus deixaria D0/D1/D2 com 20 execuções em `-30` e 10 em `-31`, e D3 com 10 em `-30` e 20 em `-31` — proporção de ambiente diferindo entre degraus. Rodar nos quatro simetricamente é melhor que rodar em alguns, porque dilui a assimetria em vez de aprofundá-la. Fator novo: `libc6` e `python3.12` mudaram em 2026-09-21 06:36, portanto o bloco de ampliação difere dos 80 anteriores também nisso.

**Lacuna de instrumentação: resolvida para séries futuras** — `run_degree.sh` grava `ambiente.json` com kernel, `boot_id`, Mesa, Vulkan, libdrm, libc6 e python por execução. Execuções até `D3/run019` seguem sem esse registro.

### Bloqueado — caminho crítico

**D4.** É o experimento decisivo: se produzir hashes idênticos, a dispersão é **exatamente zero**, resultado categórico que dispensa teste e dissolve o problema de poder dos degraus intermediários.

Ordem de execução, em `pre-registro.md` §10.7:

1. **Medir magnitude dos gradientes e distribuição de K.** **Não exige código nem a toolchain Slang** — `module.v_xy_vs`, `module.v_inv_cov_vs_opacity`, `module.v_rgb`, `module.tiles_touched` e `module.radii` já são expostos como numpy. **Pode começar imediatamente.**
2. Baixar a Slang `v2026.2.1` e verificar que o `slangc` emite SPIR-V válido para `InterlockedAdd` inteiro sobre `RWByteAddressBuffer` — **risco técnico não mitigado, sem precedente no repositório**.
3. Fixar as escalas por componente e commitar o adendo do estágio 2.
4. Implementar (4 arquivos Slang, zero C++), commitar como D4, registrar o SHA.
5. Rodar a série e verificar bit-identidade por hash.

### Não estabelecido, e é limitação a declarar

- **Nenhuma H3.x sustentada em N=20.** Fligner-Killeen só rejeita em D0 vs D3 (p = 0,034), e o IC bootstrap da razão de IQRs inclui 1,0 em todos os pares. Projeção: em N=50 o efeito **cumulativo** deve se estabelecer; a atribuição passo a passo provavelmente não.
- **Anomalia aberta:** D2 tem mais dispersão que D1 (razão de IQR 1,335), persistente de N=10 a N=20. Se sobreviver a N=50, exige explicação.

### Pendências de texto

**Prioridade alta, criada em 2026-09-21 pela busca de originalidade:**

1. **Reescrever `PLANO.md` §2.1.1, §2.1.5 e §2.5** — a afirmação de que o fenômeno não foi quantificado caiu, e o posicionamento face ao NerfBaselines deixou de ser honesto para a v2.
2. **Resolver o protocolo de seed do NerfBaselines v2.** Decide a reivindicação de isolamento a seed fixa. Caminhos: perguntar a Jonáš Kulhánek, ou inspecionar o *runner* no código aberto.
3. **Acrescentar NerfBaselines e FreeTimeGS++ ao fichamento** — hoje com zero ocorrências lá. Sugerido eixo novo, "trabalhos que reportam dispersão".
4. **Monitorar arXiv:2605.03337 até o depósito.** A deriva v1→v3 vai na direção da tese deste TCC.
5. **Reverificar as citações literais** da issue #2996 e do PR #970 — são de peso no Cap. 2 e não foram reconferidas em fonte primária nesta sessão.
6. Conferir se `percent_dense=1e-5` está mesmo na issue #89; se não, remover o número do `PLANO.md` §2.1.3.

**Anteriores:** acrescentar Efron e Tibshirani ao fichamento (o bootstrap não se ancora em Hoefler e Belli). Decidir formato ABNT para citar comentário de issue de repositório. Registrar o SHA-256 do asset da Slang. Survey `Advanced3DGS` **não localizado nem refutado** — pode ser que a anotação do fichamento esteja errada.

**Nenhum capítulo escrito.**

### Pendência institucional

**O Prof. Gilvan não foi informado de nenhum dos quatro reenquadramentos.** É o risco mais malcoberto do projeto, e o único que não depende de nada técnico.

### O que NÃO pode ser afirmado

- Que o trabalho **descobre** o não-determinismo. Kerbl o reconheceu em issue pública em 2023; um mantenedor do nerfstudio o atribuiu a atômicas de ponto flutuante em 2024. A contribuição é **quantificação e atribuição**.
- Que o tema é **inédito**. A busca de originalidade está incompleta.
- Que `-fp-mode fast` "autoriza reassociação" — a documentação do Slang não diz isso.
- Que Ubuntu 26.04 está fora da matriz do ROCm. É falso, e já custou uma reinstalação de sistema.
- Que os 20 runs de **D3** são execuções nominalmente idênticas entre si. **Não são:** metade correu sob kernel `7.0.0-30` e boot `-1`, metade sob `7.0.0-31` e boot `0`.
- Que a atualização de kernel entre os blocos de D3 **alterou** a dispersão — nem que **não** alterou. N=10 por bloco não decide.
- Que o **Mesa/RADV** mudou em algum momento das 80 execuções. **Não mudou** — `dpkg.log` não registra nenhuma transação de `mesa-*`, `libvulkan*`, `libdrm*` ou `libgl*` na janela, e o inventário de 2026-08-25 ancora `mesa-vulkan-drivers 25.2.8-0ubuntu0.24.04.2`.
- Que a atualização de `libc6` de 2026-09-21 06:36 afeta as métricas. É **hipótese plausível** pela libm no caminho do PyTorch de CPU, e não foi testada.
- Que o ciclo **N=30** foi executado. Confirmado pelo aluno em 2026-09-21 como ainda não executado.
- Que as 80 execuções já medidas correram sob ambiente congelado. **O congelamento é de 2026-09-21 e não retroage.**
- Que o fenômeno **nunca foi quantificado publicamente**. Caiu em 2026-09-21: NerfBaselines v2 reporta σ sobre quatro treinos independentes de 3DGS e gsplat no Mip-NeRF 360; FreeTimeGS++ v3 reporta média ± σ sobre dez execuções.
- Que **todo trabalho que reporta dispersão varia a seed**. **Indeterminado.** O protocolo de seed do NerfBaselines v2 não é declarado, e a v1 afirmava fixar seeds.
- Que **nenhum trabalho isola o não-determinismo**. FreeTimeGS++ isola a inicialização explicitamente: *"we fix the initialization and repeat optimization under the same protocol."*
- Que *"eles mostraram que o protocolo compromete a comparabilidade; este trabalho mostra que, mesmo com protocolo idêntico, a execução também compromete"*. **Não vale para a v2 do NerfBaselines, que mostra as duas coisas.** Reescrever `PLANO.md` §2.1.5.
- Que FreeTimeGS++ se distingue deste TCC nas quatro dimensões pretendidas **na formulação forte**. Objeto, causa e intervenção sustentam-se; a dimensão de seed está **estreitada** e precisa ser redigida como "seed fixa × seed variável com inicialização fixa".
- Que `percent_dense=1e-5` consta do corpo da issue #89. **Contestado e não reconferido.**
