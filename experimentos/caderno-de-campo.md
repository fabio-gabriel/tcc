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





## 2026-09-22 — Premissa central de D4 **confirmada no código**, e tensão de protocolo a declarar

### A confirmação

Levantamento no fork, em `HEAD detached at D3`. `src/gs_renderer.cpp:345-346`, literal:

```
RASTERIZE_BACKWARD_USE_SCHEDULING ? pipeline_rasterize_backward[(size_t)scheduled_impl][buffers.is_unsorted_1] :
    pipeline_rasterize_backward[1][buffers.is_unsorted_1],  // per-splat backward
```

Com `RASTERIZE_BACKWARD_USE_SCHEDULING` desligado — que é a intervenção de D2, e vale para tudo cumulativo depois — o pipeline é **fixo em índice `[1]`, anotado no próprio código como `per-splat backward`**.

**Isto é confirmação independente da premissa em que todo o plano de D4 se apoia** (`pre-registro.md` §10.1): que converter apenas `alphablend_shader_bwd_per_splat.slang` basta para fechar bit-identidade, porque D2 já elimina o sorteio entre implementações. Antes isso vinha de auditoria de leitura; agora vem da linha que seleciona o pipeline. A dependência D2 → D4 segue tendo de ser declarada no texto, mas deixou de ser inferência.

Também confirmado, em `src/python_bindings.cpp:654` e `:671`: `DEF_BUFFER_ARRAY(tiles_touched, int32_t, (size_t)(-1))` e `DEF_BUFFER_ARRAY(v_xy_vs, float, 2)` — os buffers são expostos ao Python como arrays tipados, como o §10.3 afirma. O `(size_t)(-1)` em `tiles_touched` sugere comprimento dinâmico, e o acessor pode exigir contagem explícita; **a assinatura ainda não foi vista e não se vai supor**.

### Decisão de método: a medição de §10.3 será feita em D3, não em D0

Registrada aqui porque muda o procedimento e não estava explícita no pré-registro.

D4 é **cumulativo sobre D3**. Medir magnitude de gradientes em D0 ou D1 mediria o estado errado: com o escalonamento ativo, o número de termos somados por acumulador difere — `A = 1` no `per_splat`, `A ∈ {8, 16, 32}` nas outras variantes (§10.4) — e o orçamento de estouro sairia incorreto. D3 também desliga o Morton, o que altera a permutação e pode alterar a distribuição de K. As escalas têm de ser derivadas do estado de código que D4 modifica, e esse estado é D3.

### Tensão de protocolo que precisa entrar como desvio declarado

`pre-registro.md` §3.2 diz, literalmente:

> *"Parâmetros de D4 a fixar antes de sua execução, em adendo datado: número de bits fracionários, faixa dinâmica assumida para os gradientes, e comportamento em saturação. Esses valores **não** podem ser escolhidos após observar a dispersão de D0–D3."*

**Essa condição já não é cumprível ao pé da letra:** a dispersão de D0–D3 foi observada em N=10, N=20 e N=30 antes de qualquer parâmetro de D4 ser fixado. A ordem real dos eventos inverteu a ordem prescrita.

A defesa existe e é boa, mas tem de ser **escrita e datada**, não assumida:

1. As escalas serão derivadas da **magnitude dos gradientes** medida em §10.3 — grandeza física do pipeline, independente da dispersão de PSNR observada.
2. O desfecho de D4 é **bit-identidade**, critério binário sobre hash de `splat.ply`. Não há liberdade para escolher escalas que "produzam" o resultado desejado: se o mecanismo não for determinístico, nenhuma escolha de escala gera hashes idênticos.
3. O que uma escala mal escolhida pode fazer é **degradar qualidade** — via o consumidor não invariante a escala em `default.slang`, que alimenta o teste de limiar de densificação (§10.5). Esse é risco de qualidade, não de inflar o resultado de H3.4.

Vai ao adendo do estágio 2 como desvio declarado. **Uma banca atenta compara datas; é melhor que o texto compare primeiro.**

## 2026-09-22 — N=30 nos quatro degraus: **H1 em 120/120, e a escada de dispersão piorou**

Série de ampliação executada na noite de 2026-09-21 sob ambiente congelado. Conferido por evidência: 30 execuções por degrau, 120 no total, commit uniforme em cada degrau e igual ao de antes.

### Integridade dos dados: nada foi perdido

O `coleta_serie.sh` reescreve o `manifest.tsv` do zero e só grava `sha256` se o `.ply` existir — risco de apagar os 80 hashes antigos. Backup feito antes (`manifest.tsv.bak-20260921`) e conferido depois: **zero linhas do backup ausentes do manifesto novo**, nos quatro degraus. O risco não se materializou.

Correção feita no `coleta_serie.sh` antes da coleta: ele **não copiava o `ambiente.json`**. Como estava, todo o registro de ambiente instrumentado em 2026-09-21 ficaria apenas na Ubuntu. Passou a copiar o `ambiente.json` por execução e os `ambiente-serie-*.json`. Testado com *fixture* real, não só `bash -n` — e nesse teste encontrei e corrigi um defeito meu: um `[ -f ... ] && cp` como último comando do corpo de laço encerraria o script sob `set -e` quando o glob não casasse.

### H1: **120 execuções, 120 hashes distintos**

30/30 em cada degrau, 120 distintos no agregado. **H1 segue confirmada de forma categórica, com metade a mais de evidência.** Continua sendo o resultado mais forte do trabalho e o único que não depende de poder estatístico.

### O bloco novo é perfeitamente homogêneo — a instrumentação funcionou

As 40 execuções novas, pelos `ambiente.json`: **todas** em `7.0.0-31-generic`, `boot_id` `1a08d41c`, `mesa-vulkan-drivers 25.2.8-0ubuntu0.24.04.2`, `libc6 2.39-0ubuntu8.9`, `python3.12 3.12.3-1ubuntu0.17`. Sem exceção nos quatro degraus.

Detalhe que justifica ter registrado pacotes e não apenas `boot_id`: as 40 novas estão no **mesmo boot** que D3 `run010`–`run019`, mas com `libc6` diferente — a atualização de 2026-09-21 06:36 ocorreu dentro daquele boot. **`boot_id` sozinho não teria detectado.**

Estratos de ambiente que isto cria:

| Degrau | kernel −30 / boot −1 / libc 8.8 | kernel −31 / boot 0 / libc 8.8 | kernel −31 / boot 0 / libc 8.9 |
|---|---|---|---|
| D0, D1, D2 | 20 | — | 10 |
| **D3** | 10 | 10 | 10 |

### H2: sustentada pelo critério, mas a margem encolheu e o estimador é instável

`39/435 = 9,0%` de pares com |ΔPSNR| ≥ 0,10 dB em D0, contra critério pré-registrado de ≥ 5%. **H2 sustentada.**

A série histórica incomoda: **17,8% (N=10) → 14,2% (N=20) → 9,0% (N=30)**, queda monotônica rumo ao limiar.

**Investiguei antes de concluir tendência, e não é tendência.** A fração de pares é uma *U-statistic* não-viesada: se as execuções viessem da mesma distribuição, seu valor esperado **não** dependeria de N. Comparando blocos de **N=10 igual**, a instabilidade fica evidente:

| | bloco 1 (000–009) | bloco 2 (010–019) | bloco 3 (020–029) |
|---|---|---|---|
| **D0** | 17,8% | 13,3% | **0,0%** |
| **D2** | 0,0% | **17,8%** | 0,0% |

D2 oscila de 0,0% para 17,8% e volta a 0,0% **dentro do mesmo degrau**. A estatística varia de zero ao máximo observado conforme o bloco. Logo os três valores de D0 não são trajetória descendente: são três amostras de um estimador muito ruidoso, e **9,0% em N=30 é a melhor estimativa disponível**, não o ponto final de uma queda.

**IC 95% bootstrap da fração, 10.000 reamostragens, seed `20260909`: `[0,9% – 18,6%]`.** Não exclui 5%. **Isto NÃO é o critério pré-registrado** — o §6 fixa o limiar de 5% sobre a fração observada, sem IC, e por esse critério H2 está sustentada. O IC entra como declaração de incerteza no texto, não como reinterpretação do critério. Acrescentá-lo ao critério agora seria alterar o protocolo depois de ver os dados.

### H3.x: **nenhuma sustentada, e o resultado andou para trás**

IQR de PSNR em N=30: D0 `0,0530` · D1 `0,0384` · D2 `0,0423` · D3 `0,0334`.

Fligner-Killeen e IC 95% bootstrap percentílico da razão de IQRs, 10.000 reamostragens, seed `20260909`, critério conjuntivo — exatamente como fixado no desvio declarado de `pre-registro.md` §5.2:

| Comparação | Fligner N=30 | (era N=20) | razão IQR N=30 | (era) | IC 95% N=30 | Veredito |
|---|---|---|---|---|---|---|
| D0 vs D1 | p = 0,310 | 0,353 | 0,725 | 0,654 | [0,338 – 1,756] | não sustentada |
| D1 vs D2 | p = 0,775 | 0,586 | 1,102 | 1,335 | [0,417 – 2,514] | não sustentada |
| D2 vs D3 | p = 0,255 | 0,055 | 0,790 | 0,484 | [0,334 – 2,019] | não sustentada |
| **D0 vs D3** | **p = 0,0548** | **0,034** | **0,631** | **0,422** | [0,276 – 1,429] | **não sustentada** |

Global nos quatro: p = 0,302, não rejeita.

**O ponto desconfortável, e ele precisa constar do texto:** em N=20 o Fligner de D0 vs D3 **rejeitava** (p = 0,034); em N=30 **não rejeita** (p = 0,0548). A razão de IQRs subiu de 0,422 para 0,631 — o efeito aparente **encolheu**. Aumentar N não aproximou o resultado do critério, afastou. É o comportamento esperado quando o efeito em N=20 estava superestimado por ruído, e é precisamente por isso que a regra manda escrutínio maior sobre achados favoráveis.

**A projeção de 2026-09-09 está refutada.** Ela previa que em N=50 o IC de D0 vs D3 iria para `[0,21 – 0,85]` e excluiria 1,0 — mas assumia a razão de 0,422 constante, com apenas o IC estreitando. Com razão de 0,631, refazendo a contração em 1/√N: N=50 daria algo como `[0,334 – 1,192]`, que **ainda inclui 1,0**. Excluir 1,0 exigiria **N ≈ 95 por degrau** — cerca de 380 execuções, da ordem de 90 horas de máquina. **Inviável dentro da janela até 06/nov.**

### Boa notícia: a anomalia de D2 está se dissolvendo, como ruído deveria

A razão de IQR D1→D2 caiu de **1,335** (N=20) para **1,102** (N=30), IC `[0,417 – 2,514]`. O candidato mais provável registrado em 2026-09-09 era ruído de amostragem, e o comportamento é o que se espera de ruído. **Não exige mais explicação física**, mas deve ser reportada como episódio, porque ilustra o risco de interpretar razão de dispersões com N pequeno.

### O achado metodológico do dia, e ele é auto-referente

Comparando blocos de N=10 do **mesmo** degrau, o IQR de D3 é `0,0131` / `0,0255` / `0,0477` — variação de 3,6× entre blocos. E D1 no bloco 1 tem IQR `0,0592`, **maior** que D0 no bloco 1 (`0,0449`), invertendo a ordenação que o desenho pretende medir.

Ou seja: **a variabilidade da medida de dispersão entre blocos é da mesma ordem que a diferença de dispersão entre degraus.** É a razão de fundo pela qual a escada não fecha — não é só falta de N, é que o efeito buscado é pequeno em relação à variabilidade da própria estatística.

É achado por si, e é elegante para o texto: **a própria medida de reprodutibilidade não é reprodutível.** O objeto de estudo reaparecendo um nível acima. Dizer com cuidado, sem retórica: o dado que sustenta é a tabela de blocos.

### Consequência para o trabalho

Reforça, agora com evidência quantitativa, a decisão já registrada: **D4 é o caminho crítico, e a escada de dispersão não é onde o trabalho se decide.** Se D4 produzir hashes idênticos, a dispersão é exatamente zero e o resultado é categórico, independente de poder. As H3.1–H3.4 passam a ser reportadas como **não estabelecidas por limitação de poder, com o N necessário calculado** — resultado honesto e defensável, e bem mais forte que um p = 0,0548 apresentado como "quase".

**Não rodar mais execuções de D0–D3 esperando que as H3.x fechem.** A conta acima mostra que não fecham. O tempo de máquina restante vai para D4.

## 2026-09-22/23 — Leitura do código do fork: três achados e um erro meu

O fork foi clonado no Mac (`code/etc/vksplatTCC`), o que permitiu ler o código em vez de inferi-lo. Tags `D0`–`D3` presentes, e **os SHAs batem exatamente com os `vksplat_commit` gravados nos `env.json` das 120 execuções** — a cadeia degrau → commit → dados está íntegra, verificada e não suposta.

### Premissa central de D4 confirmada no código

`src/gs_renderer.cpp:345-346`, literal:

```
RASTERIZE_BACKWARD_USE_SCHEDULING ? pipeline_rasterize_backward[(size_t)scheduled_impl][buffers.is_unsorted_1] :
    pipeline_rasterize_backward[1][buffers.is_unsorted_1],  // per-splat backward
```

Com o escalonamento desligado — intervenção de D2, válida para tudo cumulativo depois — o pipeline é **fixo em `[1]`, anotado no próprio código como `per-splat backward`**. Confirma a premissa de `pre-registro.md` §10.1: converter apenas `alphablend_shader_bwd_per_splat.slang` basta, porque D2 elimina o sorteio. Antes era auditoria de leitura; agora é a linha que seleciona o pipeline.

Também confirmado: `executeFusedProjectionBackwardOptimizerStep` recebe `v_xy_vs`, `v_inv_cov_vs_opacity` e `v_rgb` nos bindings **5, 6 e 7** — exatamente como o §10.2 previu.

### Imprecisão no §10.3, a corrigir no adendo

O §10.3 diz que o ponto de leitura é "após `rasterize_backward()`". Mas **`backward_optimize` não está exposto ao Python**: a lista de `.def` em `python_bindings.cpp` tem `rasterize_backward` e `train_step`, não `backward_optimize`. Do Python não há ponto entre o backward e o passo do otimizador.

O ponto viável é **após `train_step`**, e é válido por três razões verificadas:

1. `gs_renderer.cpp:323-325` — o `clearDeviceBuffer` dos três buffers está no **início** de `executeRasterizeBackward`, isto é, no passo seguinte. Os gradientes sobrevivem ao retorno de `train_step`.
2. O fused optimizer apenas lê os bindings 5/6/7.
3. `slang/default.slang`, fase `updateState`: `v_xy_vs` é declarado `StructuredBuffer<float2>` — **somente leitura**; a escrita vai para `running_grad`, que é `RWStructuredBuffer`. O `COMPUTE_SHADER_READ_WRITE` em `gs_trainer.cpp:806` é barreira conservadora, não escrita.

### O risco do §10.5 é menor do que estava registrado

`default.slang`, `computeGrowMask`: `float grad = grads.x / max(grads.y, 1.0)`. O teste de limiar da densificação usa a **média acumulada** de gradientes desde o último reset, não o valor instantâneo. Erro de quantização aleatório tende a cancelar numa média; **viés sistemático não cancela**, e truncamento é sistemático. O risco cai de "provável" para "depende do modo de arredondamento" — e isso é argumento direto para **arredondar ao mais próximo, não truncar**.

### Erro meu, do tipo que este projeto já pagou caro

A primeira versão do script de medição patcheava `st.vksplat.VkSplat` e falhou três vezes com `AttributeError: module 'simple_trainer' has no attribute 'vksplat'`.

Causa: `import vksplat` está na **linha 118, dentro da função**, não no topo do arquivo. Meu `grep` usava a âncora `^import`, que não vê import indentado. **Eu notei que o grep não listava `vksplat` e assumi mesmo assim** que o atributo existiria. A informação para não errar estava disponível; preenchi a lacuna com suposição em vez de uma verificação de dez segundos.

Correção: importar `vksplat` no script e substituir o atributo no objeto de módulo — o `import` interno resolve por `sys.modules` e recebe o mesmo objeto. Duas estratégias com fallback: patch de método, e subclasse com o método definido **no corpo da classe**. O detalhe da segunda só apareceu em teste: `Sub.train_step = ...` também usa `setattr`, e a subclasse **herda a metaclass** da base — se a base recusa `setattr`, o fallback não fallbackearia.

Barato desta vez porque falhou antes do treino, não depois de 47 minutos. **Lição operacional: `grep -n "^import"` não vê import indentado.**

## 2026-09-23 — Medição de §10.3 concluída: **D4 cabe em int32**, e um erro meu de dupla contagem

Três repetições em D3, copiadas para `pivo-reprodutibilidade-3dgs/dados/gradientes/`. Script: `experimentos/medir_gradientes_d4.py`, que **não toca o fork** — instrumenta por substituição de classe em tempo de execução, preservando os SHAs de §3.1.

### Integridade

As três repetições: `vksplat_commit d222c47182…` (D3), `train_device 0`, `strategy default`, **30.000 chamadas a `train_step` e 16 medições** em cada, nos steps 0, 1, 10, 100, 500, 1.000, 2.000, 3.000, 5.000, 7.500, 10.000, 12.500, 15.000, 20.000, 25.000, 29.999. **Zero NaN e zero Inf** nas três. Kernel `7.0.0-31-generic`, ambiente congelado.

### Erro meu, corrigido antes de concluir

Meu primeiro cálculo multiplicou `max|grad|` por `K_max` para obter o pior caso do acumulador, e concluiu que **nenhum** componente caberia em `int32` — faixas de 58 a 98 bits.

**Era dupla contagem.** O que o script lê é o gradiente **já acumulado** (leitura após `train_step`, depois de as K contribuições terem sido somadas). Multiplicar de novo por K contava a acumulação duas vezes. Refeito sobre o acumulado, cabe com folga.

Registro o erro porque a conclusão errada era dramática — "D4 inviável, exige atômico de 64 bits, quebra o zero-C++" — e teria mandado o trabalho para um redesenho desnecessário.

### Os números

Máximo do gradiente acumulado, sobre 3 repetições × 16 steps:

| componente | max global | max após step 5.000 | p99,9 máx |
|---|---|---|---|
| `xy_x` | 4,703e−05 | 1,652e−05 | 3,837e−06 |
| `xy_y` | 5,508e−05 | 2,852e−05 | 4,893e−06 |
| `conic_0` | **3,702e+03** | 3,755e+00 | 1,381e−02 |
| `conic_1` | **3,600e+03** | 1,392e+00 | 7,635e−03 |
| `conic_2` | 9,067e+02 | 8,662e−01 | 1,250e−02 |
| `opacity` | 4,482e−02 | 4,941e−03 | 2,761e−04 |
| `rgb_r` | 6,326e−03 | 2,849e−04 | 3,756e−05 |
| `rgb_g` | 5,635e−03 | 2,431e−04 | 3,886e−05 |
| `rgb_b` | 3,679e−03 | 3,572e−04 | 3,823e−05 |

Fração de zeros: **0,641** em todos os componentes — quase dois terços das gaussianas não recebem gradiente num passo dado.

**Os extremos da cônica são transiente de inicialização.** `conic_0` vai de 3,7e+03 no step 0 para 9,9e+02 no step 10 e para a ordem de 0,1–3,8 a partir do step 5.000. Três ordens de magnitude de queda. Isso obriga a dimensionar para o transiente, não para o regime estável.

### Escalas propostas, por componente

Escala `2^s` com `s = floor(log2(2^30 / max_global))` — um bit de folga sobre `2^31`:

| componente | escala | quantum | níveis no p99,9 | folga |
|---|---|---|---|---|
| `xy_x`, `xy_y` | `2^44` | 5,68e−14 | 6,8e7 / 8,6e7 | 1,4b / 1,1b |
| `conic_0`, `conic_1` | `2^18` | 3,82e−06 | 3.620 / 2.001 | 1,1b / 1,2b |
| `conic_2` | `2^20` | 9,54e−07 | 13.104 | 1,2b |
| `opacity` | `2^34` | 5,82e−11 | 4,7e6 | 1,5b |
| `rgb_r`, `rgb_g` | `2^37` | 7,28e−12 | 5,2e6 / 5,3e6 | 1,3b / 1,5b |
| `rgb_b` | `2^38` | 3,64e−12 | 1,1e7 | 1,1b |

O caso mais apertado é `conic_1`, com 2.001 níveis no p99,9 — cerca de 11 bits de resolução no corpo da distribuição. Aceitável; é consequência de a cauda transiente ser 5 ordens acima do p99,9.

### O risco do §10.5 praticamente desaparece

Com quantum de `5,68e−14` em `xy`, o erro propagado ao teste de limiar da densificação é `0,5 × q × ‖(W,H)‖ ≈ 4,2e−11`, contra `grow_grad2d = 2e−4`. **2,1e−05 % do limiar.** O candidato mais provável a fazer D4 trocar determinismo por qualidade deixa de ser preocupante — com escala por componente. Uma escala única global teria esse problema; a decisão do §10.2 de usar escalas por componente é o que o resolve, e agora há número para justificá-la.

### O ponto técnico mais importante, e ele é raciocínio meu, a verificar

**Saturação destruiria o objetivo de D4; wraparound não.**

O acumulador soma K termos quantizados, e o valor **intermediário** pode exceder o range quando há cancelamento entre termos de sinais opostos. Isso parece exigir margem enorme — mas não exige, por uma razão estrutural:

- **Aritmética modular de dois complementos é associativa e comutativa.** Se o `InterlockedAdd` fizer *wraparound*, o resultado final é correto módulo `2^32` e **independe da ordem** — que é exatamente a propriedade que D4 busca. Estouros intermediários se cancelam, desde que o **resultado final** caiba no range.
- **Saturação não é associativa.** Se a implementação saturar, o resultado volta a depender da ordem, e **D4 perde a bit-identidade** — falha em seu único objetivo.

Consequência: o §10.8, que prevê *"comportamento em saturação: contar e reportar, em vez de saturar silenciosamente"*, está formulado para o mecanismo errado. O requisito correto é **exigir wraparound e proibir saturação**, e verificar que o `slangc` emite `OpAtomicIAdd` com semântica de wraparound.

**Isto é inferência minha sobre associatividade modular, não fato verificado na spec.** Entra no adendo como afirmação a confirmar, junto com o teste do §10.6.

### Limitação da medição, a declarar

**Só o gradiente acumulado foi medido, não os termos individuais.** Portanto a magnitude dos somandos e a soma de seus valores absolutos — que governariam o estouro intermediário — não são conhecidas. Medi-las exigiria instrumentar o shader, o que sai do "zero C++ e zero Slang". O argumento do wraparound acima é o que torna a lacuna tolerável: se o resultado final cabe e a aritmética é modular, o intermediário não precisa caber. **Se o wraparound não se confirmar, esta lacuna volta a ser bloqueante.**

### Dois achados laterais que valem para o texto

**1. `K_max = 4.346` contra `p99,9 = 141`.** Confirma empiricamente a observação do §10.4 de que não há limite dedicado de tiles por gaussiana e que "uma gaussiana grande e opaca pode cobrir a tela toda". A razão entre o máximo e o p99,9 é de 31×.

**2. A divergência entre execuções é detectável no primeiro passo medido.** Comparando os 137 campos numéricos por step entre as três repetições, **apenas 71 coincidem no step 0**, caindo para ~32 no regime estável. Eu havia lido os máximos coincidentes de `conic` nos steps 0, 1 e 10 como indício de que as execuções eram idênticas no início; **conferi e estava errado** — coincidem os máximos e os campos de geometria (`K`, `radii`, que no step 0 dependem só da inicialização idêntica), mas os percentis e o mínimo não-nulo já divergem. A divergência está na cauda fina do gradiente desde o primeiro backward, antes de qualquer efeito de densificação ou de ordem de dados. **É H1 observada um nível abaixo do `splat.ply`**, e é material bom para o capítulo de mecanismo.

### Falha do script, a corrigir

O script imprime qual estratégia de instrumentação ficou ativa, mas **não grava isso no JSON**. O terminal foi perdido, e não é mais possível saber se o patch pegou por patch de método ou por subclasse. É informação de reprodutibilidade e deveria estar no `meta`. Corrigido para execuções futuras.

## 2026-09-24 — §10.6 **destravado**: o `slangc` compila `InterlockedAdd` inteiro sobre `RWByteAddressBuffer`

Teste executado na Ubuntu por `experimentos/testar_slang_atomic.sh`. Relatório em `~/tcc-runs/slang-teste/relatorio.txt`. **Este era o principal risco técnico em aberto de D4**, sem precedente em nenhum `.slang` nem em nenhum `.spv` versionado do VkSplat.

### Toolchain, verificada

- **Asset:** `slang-2026.2.1-linux-x86_64.tar.gz`, **70.742.686 bytes**, confere com o verificado em fonte primária em 2026-09-21.
- **SHA-256: `c2a05fa8643d45acf4662d7d18925ee239b16ba934da310c6cfece77dafe1927`** — **fecha a pendência** "Registrar o SHA-256 do asset da Slang". Vai ao adendo do estágio 2.
- Versão reportada pelo binário: `2026.2.1`.
- **Estrutura do tar: `bin/` na raiz**, sem diretório-raiz envolvente. Isto importa: a primeira versão do meu script fazia `tar --strip-components=1` fixo, que teria **removido o próprio `bin`** e quebrado a extração. A detecção automática foi acrescentada antes da execução, a partir do aviso na documentação oficial de que os binários ficam em `bin/`; se não tivesse sido, a instalação falharia de forma confusa.
- **`LD_LIBRARY_PATH` não definido**, e `ldd` confirma que a biblioteca vem do lugar certo: `~/opt/slang-2026.2.1/bin/../lib/libslang-compiler.so.0.2026.2.1`. O "Getting Started" do Slang avisa explicitamente que `LD_LIBRARY_PATH` sobrepõe o RUNPATH e que, com mais de uma Slang instalada (por exemplo a do Vulkan SDK), o binário pode carregar versão diferente, causando *"version mismatches and unexpected behavior"*. Num trabalho sobre reprodutibilidade numérica, compilar shaders com compilador diferente do declarado seria erro silencioso grave. **Verificado, não suposto.**
- Instalado em `~/opt/slang-2026.2.1`, fora de `/usr/local`, para o ambiente congelado em 2026-09-21 seguir rastreável. Nada instalado via apt — e vale repetir a armadilha: o pacote apt chamado `slang` é a **S-Lang**, biblioteca de terminal sem relação.

### Resultado: 6 de 6 variantes compilaram

| variante | o que testa | resultado | bytes |
|---|---|---|---|
| `v1_uint_2args` | `InterlockedAdd(addr, uint)` | OK | 796 |
| `v2_uint_3args` | idem, com `out original` | OK | 796 |
| `v3_int_negativo` | valor com sinal via `asuint` | OK | 912 |
| `v4_int_direto` | `int` sem conversão | OK | 912 |
| **`v5_nove_sitios`** | **ensaio do padrão real de D4** | **OK** | 2.908 |
| `v6_float_atomic` | controle: `InterlockedAddF32` | OK | 868 |

**O `v5` é o que destrava:** nove sítios, três `RWByteAddressBuffer`, escalas por componente e arredondamento ao mais próximo — o padrão completo previsto em §10.2 — compila para SPIR-V.

Dois detalhes úteis para escrever o patch:

- **`v3` e `v4` têm exatamente o mesmo tamanho (912 bytes)**, o que sugere que o Slang aceita `int` diretamente e faz a reinterpretação, gerando o mesmo código que `asuint` explícito. Se confirmado por comparação de hash, a macro `_ATOMIC_ADD_FIXED` pode ser escrita com `int` direto, mais legível. **Tamanho igual não é prova de código igual; conferir.**
- **`v1` e `v2` também coincidem (796 bytes)**, portanto a forma de três argumentos não custa nada quando o valor original é descartado.

### Instrução confirmada: `OpAtomicIAdd` **nativo**, sem emulação

Inspeção dos seis `.spv` com `experimentos/inspecionar_spirv.py`:

| variante | instrução atômica | extensões declaradas |
|---|---|---|
| `v1_uint_2args` | `OpAtomicIAdd` **×1** | `SPV_KHR_storage_buffer_storage_class`, `SPV_KHR_float_controls` |
| `v2_uint_3args` | `OpAtomicIAdd` **×1** | idem |
| `v3_int_negativo` | `OpAtomicIAdd` **×1** | idem |
| `v4_int_direto` | `OpAtomicIAdd` **×1** | idem |
| **`v5_nove_sitios`** | **`OpAtomicIAdd` ×9** | idem |
| `v6_float_atomic` | `OpAtomicFAddEXT` ×1 | idem **+ `SPV_EXT_shader_atomic_float_add`** |

**Zero `OpAtomicCompareExchange` em qualquer variante.** A hipótese de que o `slangc` poderia emitir emulação por compare-and-swap está descartada por inspeção do binário, não por suposição. Todos os módulos em SPIR-V 1.5.

**O `v5` emite exatamente 9 `OpAtomicIAdd`** — um por sítio, mapeamento 1:1 com os 9 sítios de `_ATOMIC_ADD` previstos no §10.2. O padrão completo de D4 não é apenas compilável: gera a instrução pretendida, na quantidade pretendida.

### Três achados que refinam o plano de D4

**1. `int` direto e `asuint` produzem código bit-idêntico.** `sha256sum` de `v3_int_negativo.spv` e `v4_int_direto.spv`: ambos `c000381b0f3697f845de807e1fddb5d231bbd8123cc8e915f475897b7f06ce6a`. Não é só o mesmo tamanho, é o mesmo módulo. Portanto a macro `_ATOMIC_ADD_FIXED` pode passar `int` diretamente, sem `asuint` explícito. **Decisão: usar `int` direto, por legibilidade.**

**2. O atômico inteiro é core SPIR-V; não exige extensão.** As variantes inteiras declaram apenas `SPV_KHR_storage_buffer_storage_class` e `SPV_KHR_float_controls`. O controle `v6` é o único que precisa de **`SPV_EXT_shader_atomic_float_add`**.

Isto é mais que detalhe de implementação, e vale para o texto: o VkSplat exige `VK_EXT_shader_atomic_float` **incondicionalmente** na criação do dispositivo (armadilha 3 do `CLAUDE.md` desta pasta). Ao converter os 9 sítios do `per_splat`, D4 **elimina a dependência dessa extensão naquele shader** — a acumulação passa a usar instrução do núcleo da especificação. A variante determinística é também a **mais portável**, e isso é argumento a favor da intervenção independente do resultado de bit-identidade. Não estava previsto no pré-registro.

Ressalva de escopo, para não exagerar: a extensão continua necessária pelas **outras** variantes de backward (`per_pixel`, `tensor`) e pelos 6 sítios de `morton_sort.slang`, que D4 não toca. A afirmação correta é sobre o shader convertido, não sobre o binário todo.

**3. `SPV_KHR_float_controls` aparece nos seis módulos**, o que confirma que `-denorm-mode-fp32 preserve` **foi efetivamente aplicado** — a opção não foi silenciosamente ignorada. Evidência de que a lacuna do §10.8 é controlável na prática, não apenas nominalmente.

### O que este teste ainda NÃO estabelece

1. ~~Se a instrução emitida é `OpAtomicIAdd` nativo ou emulação por compare-and-swap.~~ **Resolvido em 2026-09-24: nativo, zero compare-exchange.** Resolvido sem instalar `spirv-tools`, por `experimentos/inspecionar_spirv.py`, que parseia o binário direto — cabeçalho de 5 palavras, opcode nos 16 bits baixos da primeira palavra de cada instrução. Validado antes do uso com módulos sintéticos cobrindo `OpAtomicIAdd` nativo, emulação por compare-exchange, atômico de ponto flutuante, big-endian e módulo corrompido.
2. ~~Se `OpAtomicIAdd` faz wraparound e não saturação em estouro.~~ **Resolvido em 2026-09-24 na especificação SPIR-V — ver a entrada seguinte.**
3. **Se o RADV executa a instrução corretamente em `gfx1201`.** Compilar não é executar, e isso só a série de D4 responde.

### Opções fixadas na invocação, e por quê

`-fp-mode precise`: não autorizar transformações de ponto flutuante num teste cujo objeto é comportamento numérico. Lembrando a correção de 2026-09-21: a documentação do Slang **não** afirma que `fast` autoriza reassociação — dizer isso segue proibido.

`-denorm-mode-fp32 preserve`: o §10.8 aponta que o `compile_shaders.py` do VkSplat **não fixa** essa opção, cujo default é *"implementation defined"*. Fixada aqui. Para o degrau D4 em si, a decisão de fixá-la ou declarar como limitação do artefato tal como distribuído continua aberta.

## 2026-09-24 — Especificação SPIR-V: **wraparound confirmado**, e a consequência é mais forte do que se esperava

Fonte: especificação SPIR-V unificada, versão 1.6 revisão 8, Khronos Group, em `registry.khronos.org/SPIR-V/specs/unified1/SPIRV.html`. Acesso em 2026-09-24. Esta era a última peça pendente do adendo do estágio 2.

### A cadeia normativa, em duas cláusulas

**§3.3.18, `OpAtomicIAdd`** — citação literal:

> *"Perform the following steps atomically with respect to any other atomic accesses within Memory to the same location: load through Pointer to get an Original Value, get a New Value by **integer addition** of Original Value and Value, and store the New Value back through Pointer."*

**§3.3.13, `OpIAdd`** ("Integer addition of Operand 1 and Operand 2") — citação literal:

> *"The resulting value equals the **low-order N bits of the correct result R**, where N is the component width and R is computed with enough precision to avoid overflow and underflow."*

Portanto a adição inteira em SPIR-V é definida como os N bits baixos do resultado exato: **aritmética modular `2^N`**. Não há saturação, e não há comportamento indefinido em estouro.

**Força da inferência, declarada:** a entrada de `OpAtomicIAdd` **não** repete a cláusula dos "low-order N bits"; ela diz *"integer addition"*, e a semântica de adição inteira está definida em `OpIAdd`. A conclusão vem da **composição de duas cláusulas normativas**, não de uma frase única. É inferência de uma etapa, e não de uma leitura literal — consta assim no texto, e não como "a especificação diz que `OpAtomicIAdd` faz wraparound".

**Ressalva de escopo:** a especificação afirma que o client API pode acrescentar regras e limitações. Não se verificou se a especificação Vulkan restringe algo aqui. A afirmação verificada é no nível SPIR-V.

### Por que isso é o fundamento teórico de D4

Adição modular `2^32` é **associativa e comutativa**. Logo a soma das K contribuições atômicas produz o mesmo resultado **qualquer que seja a ordem** em que as invocações de GPU executem. Esse é exatamente o mecanismo que H3.4 propõe, e agora está ancorado na especificação em vez de na intuição.

Simetricamente, confirma a razão pela qual o `float32` falha: adição em ponto flutuante não é associativa, e é essa não-associatividade — combinada com ordem não determinística — que produz os 120 modelos distintos de H1.

### A consequência que separa dois riscos, e não estava prevista

Como a aritmética é modular e não saturante, **o estouro intermediário não quebra a bit-identidade**. Mais: **o estouro do resultado final também não quebra.** Um acumulador que exceda o range produz um valor numericamente errado — mas produz *o mesmo* valor errado em toda execução.

Isso separa dois riscos que estavam confundidos no plano:

| risco | garantido por | sensível à escala? |
|---|---|---|
| **Bit-identidade** (H3.4) | wraparound modular | **não** |
| **Correção numérica / qualidade** (PSNR, contagem de gaussianas) | escala bem dimensionada | **sim** |

**Consequência de método, e ela fortalece o argumento registrado em 2026-09-22:** a preocupação do §3.2 de que "os parâmetros de D4 não podem ser escolhidos após observar a dispersão de D0–D3" fica ainda mais dissolvida. A escala **não pode** influenciar o desfecho de H3.4, porque o determinismo vem do wraparound e vale para qualquer escala. O que a escala afeta é a qualidade — que é observável reportado, não critério de hipótese. Não há grau de liberdade pelo qual a escolha tardia das escalas pudesse favorecer o resultado.

**Consequência prática:** se D4 produzir hashes idênticos mas PSNR degradado, isso **não** é falha de H3.4 — é evidência de escala mal dimensionada, diagnosticável e corrigível, e os dois efeitos são distinguíveis nos dados. Se produzir hashes distintos, o problema não está na escala: está em alguma fonte de não-determinismo fora dos 9 sítios convertidos.

### Correção ao §10.8 do pré-registro

O §10.8 prevê *"comportamento em saturação: contar e reportar, em vez de saturar silenciosamente"*. **A formulação está errada para esta plataforma:** não existe saturação em adição inteira SPIR-V. O item deve ser reescrito como:

- **exigir** semântica de wraparound (que é o comportamento especificado, não uma opção);
- **contar e reportar estouro do resultado final**, porque afeta correção numérica embora não afete bit-identidade;
- **proibir** qualquer implementação com `clamp`/`min`/`max` antes do atômico, porque isso reintroduziria não-associatividade e destruiria o objetivo do degrau.

Este último ponto é o mais importante e o menos óbvio: uma tentativa bem-intencionada de "proteger contra estouro" saturando o valor antes da adição **quebraria D4**. Registrar no adendo de forma explícita, para que não seja acrescentado como "melhoria" durante a implementação.

### Estado do §10.7

| passo | estado |
|---|---|
| 1. Medir magnitude dos gradientes e distribuição de K | **feito** (2026-09-23) |
| 2. Verificar que o `slangc` emite SPIR-V válido para `InterlockedAdd` inteiro | **feito** (2026-09-24) — `OpAtomicIAdd` nativo ×9 |
| 3. Fixar escalas por componente e commitar o adendo do estágio 2 | **pronto para redigir** |
| 4. Implementar (4 arquivos Slang, zero C++), commitar como D4, registrar SHA | pendente |
| 5. Rodar a série e verificar bit-identidade por hash | pendente |

**Nada mais bloqueia o adendo.** Os insumos estão todos verificados: escalas por componente, SHA-256 da toolchain, instrução confirmada, semântica de estouro ancorada na especificação, e a dependência D2 → D4 confirmada no código.

## 2026-09-25 — Adendo do estágio 2 redigido, e **dois itens do plano estavam errados**

Sessão principal, depois de reler o caderno em disco. O caderno avisa, e com razão, que a memória da conversa estava desatualizada.

### Conferência de retomada

Tudo que a seção de estado afirma foi conferido por evidência:
- 30 execuções por degrau;
- 120 hashes, todos distintos;
- `ambiente.json` só em `run020`–`run029`;
- 3 JSON de gradientes, cada um com 30.000 chamadas, 16 medições e zero NaN/Inf;
- D0 com IQR 0,0530 e H2 = 39/435.

**Divergência encontrada:** não havia commit posterior a `c222800`. As entradas de 2026-09-24 sobre SPIR-V, os achados do `slangc` e a seção "Estado em 2026-09-25" existiam **só no working tree**. Os scripts estavam commitados; as conclusões tiradas deles, não. Informado ao aluno. O commit é dele.

### Redigido: `pre-registro.md` §11, acrescentado ao fim

**Nenhuma linha do §0 ao §10 mudou.** Conferido com `cmp` das linhas 1–355 contra HEAD: bit-idênticas, zero linhas removidas. O §11 é rascunho. Fica vinculante quando commitado, e só depois do teste T0.

### Achado 1 — o compilador é um fator não controlado, e o plano não o via

Lido no fork, em D3:

- **O `.spv` versionado é o que executa.** O `setup.py` não compila shaders. Os 45 `.spv` de D3 são os do upstream: `git diff b3ad2b0 D3 -- '*.spv'` sai vazio. D0–D3 nunca executaram shader compilado por nós.
- **O compilador do upstream não é identificável.** Os 42 `.spv` do Slang têm `generator 0x280000`, que é tool 40 com versão **0**.
- **Mexer em um arquivo regenera muitos.** O `compile_shaders.py` recompila por grupo, e o checksum inclui dependências e o próprio script. Alterar o `per_splat` recompila as **6** saídas de `alphablend_shader.slang`, **inclusive o `rasterize_forward`**. Alterar `default.slang` recompila as 9 fases. `config.slang` é dependência de 8 dos 12 grupos, e `utils.slang` de 4.

Logo D4 terá `.spv` gerados pelo nosso `slangc 2026.2.1`. Se ele não reproduzir os bytes do upstream a partir das mesmas fontes, D4 difere de D3 **em duas coisas**.

**H3.4 não é afetada**, porque bit-identidade é propriedade interna de D4. **A comparação D3 × D4 de tempo e de qualidade, sim.**

Resposta: teste **T0**, `experimentos/reproduzir_spv_upstream.py`. Ele recompila as fontes inalteradas de D3 nos 41 jobs Slang, com o comando exato do `compile_shaders.py` e com a lista de jobs importada dele, e compara por hash. O adendo pré-registra dois caminhos: A, se tudo for idêntico; B, se algo diferir. No caminho B há um controle **D3c**, fixado antes dos dados (§11.5).

O script foi testado no Mac com clone descartável e `slangc` falso. Enumera 41 jobs, 16 deles nos grupos de D4. Detectou o byte corrompido de propósito no offset certo e deixou o fork limpo. Um defeito foi encontrado e corrigido nesse teste: o `import` do `compile_shaders` criava `__pycache__` dentro do fork. O git não acusava porque está no `.gitignore`, mas era escrita no fork, contra o que o script promete.

**Não pôde ser testado aqui:** o `slangc` real. Ele está só na Ubuntu.

Achado lateral: há 42 `.spv` Slang versionados e só 41 jobs. O órfão é `rasterize_backward.spv`, do *initial commit*, que **não é carregado** (`spirv_paths` só lista os índices 0 a 4). É arquivo morto.

### Achado 2 — o item 2 do plano do adendo estava errado

A seção de estado mandava fixar `-fp-mode precise` e `-denorm-mode-fp32 preserve` para D4. Evidência contra:
- o upstream compila com `-stage compute -O -fp-mode fast -line-directive-mode none` (`compile_shaders.py:26`);
- **nenhum dos 42 `.spv` Slang do upstream declara `SPV_KHR_float_controls`**;
- os `.spv` do teste de 2026-09-24, compilados com `preserve`, declaravam.

Fixar essas opções em D4 mudaria o binário por uma segunda razão. **Corrigido no adendo:** D4 usa as opções do upstream, e o modo de denormais fica declarado como limitação idêntica nos cinco degraus. Essa é uma das duas alternativas que o §10.8 já previa.

### Achado 3 — o item 6 do plano estava errado, e ao contrário

O plano proibia `clamp`/`min`/`max` antes do atômico, dizendo que isso reintroduziria não-associatividade. **Fui à especificação** (SPIR-V 1.6, Revision 8, *Last updated 2026-09-08*, acesso em 2026-09-25). Sobre `OpConvertFToS`, literal:

> *"with round toward 0.0 […] Behavior is undefined if Result Type is not wide enough to hold the converted value."*

Daí:
- **sem `clamp` por termo, um termo fora do range é comportamento indefinido.** O item 6, como estava, proibia justamente a proteção necessária;
- `clamp` por termo é função pura do termo, e a soma modular de funções puras dos termos continua independente da ordem. O que destruiria a associatividade é saturar o **acumulador**, por exemplo com um laço de compare-exchange com `min`/`max` sobre o valor armazenado;
- **a conversão trunca.** Arredondamento ao mais próximo exige `round` explícito, o que confirma com fonte o que o caderno de 2026-09-22 argumentava sobre viés.

A regra do adendo passa a ser: **exigir `clamp` por termo e proibir saturação do acumulador.** O erro não afetava resultado, porque nada foi implementado. Teria feito a implementação de D4 depender de comportamento indefinido.

Na checagem da especificação, um regex meu acusou "aviso de obsolescência". **Conferi o trecho literal: era o changelog falando de `WorkgroupSize`.** A revisão 8 do caderno também foi confirmada, depois de outro regex meu falhar ao atravessar quebra de linha. Os dois são falsos alarmes meus, registrados porque o padrão de 2026-08-25 começou exatamente assim.

### Achado 4 — a premissa do §10.1 confirmada no laço, não só na seleção do pipeline

O `per_splat` escreve `v_pixel_state[pix_rank]` em memória compartilhada dentro do laço. Isso poderia ser corrida, o que invalidaria a premissa de determinismo da pré-redução. **Não é.** `per_splat.slang:138-178` é um pipeline em diagonal: no passo `i`, o splat `s` processa o pixel `p = i − s`. Há um único dono por pixel por passo e barreira em todo passo. A premissa favorece a tese, e por isso foi lida no código em vez de aceita.

### Decisões de desenho registradas no adendo

- Novo arquivo `d4_fixed_point.slang`, fonte única das escalas para produtor e consumidores.
- **`config.slang`, `utils.slang` e `compile_shaders.py` intocados**, pela cascata de recompilação.
- **Invariante V2:** o diff D3 → D4 contém exatamente 3 `.slang`, o arquivo novo e 3 `.spv` (`rasterize_backward_1`, `fused_projection_backward_optimizer`, `default_update_state`).
- Escalas por componente, recalculadas dos JSON: `s` = 44, 44, 18, 18, 20, 34, 37, 37, 38, com folga de 2,1× a 2,8× sobre o máximo observado.
- Sete desvios declarados (D-1 a D-7) e oito limitações.

## 2026-09-25 — T0 executado: **o `slangc 2026.2.1` reproduz bit a bit os `.spv` do upstream**

Executado na Ubuntu, com o fork em D3 e `LD_LIBRARY_PATH` removido. Saída literal:

```
slangc: 2026.2.1
jobs Slang: 41  ->  {'IDENTICO': 41}
grupos que D4 altera: 16/16 identicos ao upstream
VEREDITO T0: REPRODUZ o upstream: o compilador NAO e fator de confusao
relatorio: /home/fabio/tcc-runs/spv-repro/reproducao.json
```

**Consequência:** vale o **caminho A** do `pre-registro.md` §11.5. D4 difere de D3 só na fonte dos 3 `.slang` e no arquivo novo. O controle D3c **não se aplica**. A comparação D3 × D4 de tempo e qualidade não fica confundida pelo compilador.

**O que o resultado permite e não permite dizer:**
- Permite dizer que o nosso compilador, com as opções do upstream, gera exatamente os mesmos bytes a partir das fontes de D3, nos 41 jobs Slang.
- **Não prova** que o upstream usou a versão 2026.2.1. Prova que usou uma versão que gera a mesma saída para essas fontes. Isso é consistente com o README do VkSplat (`README.md:112` em D3, literal: *"Tested with `slang-2026.2.1-linux-x86_64`, other versions may also work"*, conferido em 2026-09-25), mas é consistência e não prova.
- Não cobre os 3 `.spv` do `radix_sort`, gerados pelo `glslc`. D4 não os toca.

**Escrutínio pendente, por ser resultado favorável.** O terminal mostra só a contagem. Antes de o §11 ser commitado, conferir no `reproducao.json` que:
- os 41 `sha256_nosso` são **distintos entre si** (não é um mesmo arquivo comparado 41 vezes);
- `bytes_nosso` é igual a `bytes_upstream` e não nulo;
- `returncode` é 0 em todos;
- `stdout_stderr` está vazio (sem avisos do compilador).

O script já garante as duas primeiras condições por construção, porque compara o arquivo gerado em diretório temporário com o versionado. A conferência no dado é a prova, e a garantia do código não a substitui.

**Conferido em 2026-09-30**, depois de o JSON entrar em `2f2ad65`:
- 41 `sha256` distintos entre si;
- nosso = upstream em todos;
- tamanhos iguais, de 1.624 a 148.488 bytes;
- `returncode` 0 e saída do compilador vazia em todos.

**A ordem dos eventos é demonstrável pelo git:** o §11 com os dois caminhos entrou em `02722af` às 17:57:49 −03, e o T0 foi gerado às 18:01:26 −03 (`gerado_em` = 21:01:26Z), 3 min 37 s depois. Registrado no `pre-registro.md` §11.10, acrescentado sem editar §11.1–§11.9. **Com o commit do §11.10, o adendo fica vinculante para D4.**

## 2026-09-25/30 — `.ply` de D0–D3 movidos para o HD externo, verificados por hash

**Motivo.** Havia 17–21 GB livres no SSD, contra ~15 GB necessários só para as saídas de D4 com N=10 (1,51 GB por execução, pela soma de `dir_total_bytes` dos manifestos). Os diretórios de D0–D3 somam 181,3 GB, dos quais 164,0 GB são `splat.ply`.

**Decisão:** mover os artefatos **antigos** e manter os **novos** no SSD. D4 grava no mesmo disco e no mesmo caminho que D0–D3 (`~/tcc-runs/series/`), para não introduzir um fator evitável. Um disco USB que desconecta no meio da série derrubaria execuções.

**Destino:** `/media/fabio/Seagate Expansion Drive/tcc-runs-arquivo/`, `/dev/sda1`, **NTFS via `ntfs3`**, 932 GB, 550 GB livres antes da cópia.

**Procedimento:**
- `rsync -rt`, e não `-a`: o NTFS não guarda dono e permissões Unix, e `-a` produziria erros espúrios que esconderiam um erro real;
- conferência do `sha256` de cada `splat.ply` copiado contra o `manifest.tsv` versionado;
- remoção **só dos `splat.ply`** do SSD, e só se o degrau desse exatamente 30 ok e 0 falhas;
- JSON, logs e PNG permaneceram no SSD.

**Evidência:**
- D0: `rsync` saiu com 0 (45.198.560.907 bytes, 912 arquivos); verificação **30 ok, 0 falhas**.
- D1–D3: laço com a trava automática. As linhas por degrau não foram transmitidas. A evidência indireta é `find ~/tcc-runs/series -name splat.ply` = **0** no SSD e **120** no HD. Como o laço só apagava depois de 30/30, zero no SSD implica que a trava passou nos três.
- `df -h /` depois: 245G, 73G usados, **160G livres**.

Um susto de colagem foi conferido e descartado: no texto colado faltavam `$`, o que poderia significar cópia para `dados/D0/DEST/` dentro do repositório. `ls -d` confirmou que esse diretório não existe, e o uso de disco é incompatível com 45 GB extras.

**Consequência para o §7 do pré-registro:** os `.ply` de D0–D3 têm hoje **cópia única**, num HD USB, contra o *"disco local e cópia em nuvem"* previsto. H1 continua verificável pelos hashes versionados. Mas perder o HD eliminaria a possibilidade de reconferir contra os arquivos, e de fazer as análises secundárias do §4 (diferenças por parâmetro entre pares). **Pendência:** cópia em nuvem, com o local registrado aqui.

**Não verificado:** a identidade dos dois volumes SSD internos desmontados (731 GB e 499 GB). O de 499 GB pode ser a *"partição extensível a ~500 GB"* do §7. `lsblk -f` não foi executado.

## 2026-09-30 — Patch de D4 escrito e verificador pronto; **nada compilado com o `slangc` real ainda**

Escrito no Mac, no clone de leitura, branch local `d4-rascunho` criada a partir de D3, **sem commit**. Entregáveis no repositório do TCC:
- `experimentos/d4/d4.patch`, com 207 linhas;
- `experimentos/compilar_d4.py`.

### O patch, conforme `pre-registro.md` §11.4

`+119/−24` em 4 arquivos, todos em `vksplat/slang/`:

| arquivo | mudança |
|---|---|
| `d4_fixed_point.slang` (novo) | 9 escalas `2^s`, 9 inversos `2^−s`, `D4_LIM = 2147483520.0`; `d4_quantizar(v,s) = int(round(clamp(v·s, −L, L)))`; três funções de desquantização |
| `alphablend_shader_bwd_per_splat.slang` | `#include` do novo arquivo; macro `_ATOMIC_ADD_FIXED` substitui o bloco `#if USE_EMULATED_F32_ATOMIC` (`:183-189`); 9 sítios com escala por sítio |
| `fused_projection_backward_optimizer.slang` | bindings 5/6/7 para `int2`/`int4`/`int`; desquantização em `:110-115`; `rgb` lido localmente, sem `read_t3_float3` |
| `default.slang` | `#include` **dentro** do bloco `#if DEFAULT_PHASE == UpdateState`, para as outras 8 fases não verem o arquivo; binding 0 para `int2`; desquantização em `:70` |

Intocados: `config.slang`, `utils.slang`, `compile_shaders.py` e todo o C++.

### Decisões tomadas lendo o código, não supondo

- **A forma da chamada atômica é a que já compilou.** `buffer.InterlockedAdd(endereço, asuint(int))` é a forma do ensaio `v5_nove_sitios` de 2026-09-24, que gerou `OpAtomicIAdd` ×9. O endereço usa `(address)*sizeof(float)`, a expressão do código original, já aceita pelo `slangc` neste arquivo. Uma primeira versão minha usava `sizeof(int32_t)`, forma não verificada, e foi revertida.
- **`rgb_b` usa `2^38`, o valor do adendo**, e não os `2^37` usados para os três canais no ensaio `v5`.
- **Literais das constantes gerados por script.** Cada um foi conferido: lido como `float32`, dá exatamente `2^s`, e `D4_LIM` é o maior `float32` abaixo de `2^31`. Escala divergente entre produtor e consumidor seria erro silencioso.
- **O produtor afeta só `rasterize_backward_1`.** `alphablend_shader.slang:284-285` inclui o `per_splat` apenas quando `BACKWARD_MODE == PER_SPLAT`.
- **Zero C++, reconfirmado.** O C++ declara os buffers como `Buffer<float>` (`buffer.h:116-119`), o que só determina o tamanho: 4 bytes por elemento, o mesmo de `int32`. Além disso, só zera, faz barreira e vincula. `tcc-base` = D3 = `d222c47182…`, então D4 entra em cadeia linear.
- `g_idx` no otimizador é `uint` (`:95`), o mesmo tipo que o `read_t3_float3` recebia. A indexação `3*g_idx+k` é idêntica à original.

### O verificador, `compilar_d4.py`

Compila os 16 jobs dos 3 grupos com o comando de T0 e executa V2, V3 e V4 do §11.6. **Não commita.** Aborta se o fork não estiver exatamente em "D3 + fontes de D4".

**Todos os números de instrução foram conferidos literalmente nas especificações**, baixadas de novo para `/tmp` porque a cópia de 25/09 tinha sido apagada:
- SPIR-V 1.6 rev. 8: `OpExtInstImport` = 11, `OpExtInst` = 12, `OpConvertFToS` = 110, `OpConvertSToF` = 111, `OpAtomicIAdd` = 234.
- GLSL.std.450, rev. 17: `Round` = 1, `RoundEven` = 2, `FMin` = 37, `FMax` = 40, `FClamp` = 43, `NMin` = 79, `NMax` = 80, `NClamp` = 81.

Nessa leitura, três regex meus deram resultado errado ou cortado. `Round` e `RoundEven` saíram com o texto trocado, e `OpExtInst*` escapou porque o número de palavras é variável. **Os três foram resolvidos lendo o trecho literal**, e nenhum número entrou no script por regex não conferido.

Sobre `Round`, literal: *"The fraction 0.5 rounds in a direction chosen by the implementation"*. Coerente com o §11.2, que declara a regra de desempate irrelevante para H3.4.

### Testes feitos aqui, e o que eles não cobrem

- **Parser validado em dados reais.** Nos `.spv` de D3, o `rasterize_backward_1` mostra **exatamente 9 `OpAtomicFAddEXT`** e `SPV_EXT_shader_atomic_float_add`, que são os 9 sítios substituídos. Os dois consumidores não têm atômico nenhum, o que dá a linha de base de V4.
- **Patch** aplica limpo com `git apply --check` num clone descartável em `tcc-base` = D3, e o conteúdo aplicado é idêntico ao rascunho.
- **Caminho negativo.** Com um `slangc` falso que devolve os bytes de D3, **todos** os critérios de D4 falham, e o código de saída é 2, "não commitar". Não há aprovação por engano.
- **Pré-condição.** Um arquivo intruso na árvore faz o script abortar antes de compilar.
- **Não testado:** o caminho positivo e a própria compilação. Exigem o `slangc` real, que só existe na Ubuntu. É o primeiro ponto em que o patch pode falhar, e erro de compilação é resultado barato.

## 2026-09-30 — D4 compila na primeira tentativa e **passa V2, V3 e V4**

Patch aplicado na Ubuntu sobre `tcc-base` = D3, e `compilar_d4.py` executado. Saída literal, resumida:

```
compilados: 16 jobs, 0 falhas, 0 com saida (avisos)
V2 OK   conjunto alterado vs D3
V3 OK   rasterize_backward_1.spv   (OpAtomicIAdd == 9, OpAtomicFAddEXT == 0, sem SPV_EXT_shader_atomic_float_add)
     deltas vs D3: round=9 clamp=9 minmax=0 ConvertFToS=9
V4 OK   consumidores (atomicos inalterados; OpConvertSToF aumentou nos dois)
VEREDITO: PRONTO PARA COMMIT DE D4
```

**Leitura.** O critério de V3 exigia aumentos de pelo menos 1. Os deltas saíram **exatamente 9 em cada**: um arredondamento, um `clamp` (como `FClamp`/`NClamp`, e não como par min/max) e uma conversão por sítio. É evidência mais forte que o critério pedia de que o binário corresponde ao código.

**V2 é também uma segunda reprodução do T0.** Dos 16 `.spv` recompilados, 13 saíram bit-idênticos a D3. Isso confirma, no binário, que o `#include` do `per_splat` só alcança `BACKWARD_MODE == PER_SPLAT` e que as outras 8 fases de `default.slang` não foram afetadas.

**Não estabelecido:** que D4 executa corretamente no RADV. Compilar e emitir as instruções certas não é executar, e isso só a série responde (§11.9, item 1).

**Pendente antes da série:**
1. commit e tag `D4` no fork (V1);
2. cópia de `verificacao_d4.json` para `dados/toolchain/`;
3. conferência independente, a partir do Mac, do commit empurrado;
4. entrada datada §11.11 com o SHA de D4, commitada no TCC.

O §11.10 já está no remoto (`6bc589d`), e o adendo está vinculante.

## 2026-09-30 — D4 commitado e conferido de forma independente

### Commit e conferência independente

**D4 = `22560858b0f23586176ea3bf03907c607d8c944f`**, 2026-09-30 19:09:08 −03, `tcc-base`, tag leve `D4`, com D3 como pai. Relatório `verificacao_d4.json` em `ce1d913` (gerado 19:05:38 −03, antes do commit).

Conferido a partir do Mac, sobre o que foi empurrado:
- `git diff --name-status D3 D4` dá exatamente os 7 arquivos;
- as 4 fontes são bit-idênticas ao rascunho de que saiu o patch;
- os 3 `.spv` têm o mesmo `sha256` que o verificador aprovou;
- o perfil foi reproduzido: `rasterize_backward_1` tem `OpAtomicIAdd` ×9, `FClamp` ×9 e **`Round`** ×9 (não `RoundEven`, caso previsto no §11.2), e `OpConvertFToS` passa de 1 para 10.

Nos consumidores, `OpConvertSToF` passou de 8 para 17 no otimizador e de 1 para 3 em `UpdateState`: exatamente o número de componentes desquantizados em cada um. Registrado no `pre-registro.md` §11.11, acrescentado ao fim.

## 2026-10-01 — Série D4, N=10: **H3.4 refutada**, mas a dispersão colapsa e a divergência é empurrada para o fim do treino

Série executada em 2026-09-30, coletada em `de8693f`. O §11.11, com o SHA de D4, foi commitado em `b8b766d`. Isso aconteceu **depois** de a série rodar. Os parâmetros (§11.1–§11.10) e o commit e a tag de D4 já estavam no remoto antes da primeira execução.

### Integridade, conferida antes de ler qualquer resultado

As 10 execuções:
- todas com `vksplat_commit` = `22560858b0f2…`, árvore limpa e `train_device 0`;
- todas no mesmo boot (`8d0e782c`), com kernel `-31`, Mesa `25.2.8-0ubuntu0.24.04.2`, `libc6 8.9` e `python 0.17`, o mesmo estrato do bloco `run020`–`run029`;
- dispositivo `AMD Radeon RX 9070 XT (RADV GFX1201)`, com o `llvmpipe` marcado `NOT VIABLE`, sem `USE_EMULATED`;
- contagens do escalonador `PerSplat`/`Tensor` em **0/0**: o escalonamento está desligado, como em D2 e D3.

O resultado desfavorável recebeu a mesma conferência de harness que um favorável receberia.

### H3.4 — refutada pelo critério do §6

**10 execuções, 10 hashes de `splat.ply` distintos.** O critério é a identidade de hash, e ela falhou. Conforme o §11.8, a fonte residual não identificada passa a ser o achado.

### Mas a magnitude da dispersão desabou

| | D3, `run020`–`run029` | D4 | razão |
|---|---|---|---|
| IQR de PSNR | 0,0477 dB | **0,0038 dB** | ~12× |
| amplitude de PSNR | 0,0746 dB | 0,0243 dB | ~3× |
| IQR de nº de gaussianas | 10.202 | **18** | ~570× |
| amplitude de nº de gaussianas | 29.903 | **104** | ~290× |
| valores distintos de nº de gaussianas | 10/10 | **6/10** | — |

Cinco das dez execuções terminam com exatamente 5.940.143 gaussianas, e `splat.ply` de tamanho idêntico, mas com hashes diferentes.

A amplitude de PSNR é puxada por uma única execução, `run001` (27,0165 contra 26,992–27,000 das outras nove). Com N=10, isso é descrição e não teste. Comparação formal com D3 pelo §5.2 ainda não foi feita.

### O achado mais forte: onde as trajetórias divergem

Pelas 144 linhas de densificação de cada log (`N dupli, N split, N prune -> N splats`), grandeza secundária pré-registrada no §4:

| | primeiro evento de densificação em que as execuções divergem | sequências completas distintas |
|---|---|---|
| D3, `run020`–`run029` | **evento 0** de 144 | 10 de 10 |
| D4 | **evento 129** de 144 | **6 de 10**; um grupo de **5 execuções idênticas nos 144 eventos** |

Em D3, as execuções já diferem na primeira densificação. Em D4, as dez são idênticas em 129 das 144, e no evento 129 diferem por 1 a 4 gaussianas em 5,7 milhões. **D4 transformou um não-determinismo que se manifesta de imediato num evento raro e tardio.**

Isso é compatível com a eliminação da fonte dominante e com a persistência de uma fonte residual rara. **Não identifica a fonte residual.** As cinco execuções com densificação idêntica também têm hashes diferentes, então a divergência pode estar também nos valores dos parâmetros, sem cruzar nenhum limiar de densificação.

### Custo em qualidade: alto, e provavelmente não é o custo do determinismo

| | D3, `run020`–`run029` | D4 |
|---|---|---|
| PSNR mediana | 27,383 dB | **26,998 dB** (−0,39) |
| SSIM | 0,8638 | 0,8471 |
| LPIPS-Alex | 0,0760 | 0,0998 |
| nº de gaussianas | 5,81 M | 5,94 M (+2,3%) |

−0,39 dB é quase quatro vezes o limiar de relevância de H2.

**Hipótese, com base quantitativa, ainda não testada:** a quantização zera praticamente todo o gradiente de **cônica**. Nos dados de `dados/gradientes/` (passos ≥ 1000), o percentil 99 do gradiente **já acumulado** de `conic_0`, `conic_1` e `conic_2` vale **0,3, 0,3 e 0,7 quantum**. Cada termo individual, antes de somar os K tiles, é menor ainda, e abaixo de ½ quantum vira zero. Nos demais componentes a resolução é ampla: o p90 fica em 2.000 a 260.000 quanta. Se a hipótese se confirmar, D4 tem efetivamente **duas** alterações em relação a D3: a acumulação inteira e a supressão do gradiente de covariância. Nesse caso, a perda de qualidade não pode ser atribuída ao determinismo.

### Erro meu, na origem da hipótese

O §11.2 fixa `s = floor(log2(2^30 / máximo))`. Na cônica, o máximo é o transiente do passo 0 (3,7e+03), cinco ordens acima do regime. Ao redigir o adendo, julguei aceitáveis os "2.001 níveis no p99,9" de `conic_1`. **Aquele p99,9 era o máximo entre todos os passos, dominado pelo início do treino. Não olhei o regime.** O dado para ver isso estava no JSON desde 2026-09-23. É o mesmo padrão do erro de dupla contagem daquela data: uma estatística agregada sem olhar a estrutura temporal. A regra estava pré-registrada e foi seguida; o erro é de desenho, não de execução, e entra como limitação de D4.

### Tempo

D4 tem mediana de **870,5 s**, contra 945,6 s de D3, ou seja **8% mais rápido**. Pelo T0 (caminho A), o compilador não é fator de confusão. Mas, se a hipótese da cônica valer, parte do trabalho do backward pode estar sendo descartada. Fica registrado como observação, sem interpretação.

### Próximos passos possíveis, a decidir com o aluno

1. **Diagnóstico sem execução nova:** comparar os `splat.ply` de D4 na Ubuntu, sobretudo dentro do grupo de 5 trajetórias idênticas. Ver quantas gaussianas diferem, em quais parâmetros, com que magnitude, e se a diferença é só de ordem dos registros. É a grandeza secundária "diferenças por parâmetro" do §4, já pré-registrada.
2. **Variante com escala de cônica dimensionada para o regime:** separaria o artefato de quantização do custo do determinismo. Exige adendo novo, datado, **antes** de rodar, e declarado como posterior à observação de D4. São ~2,5 h de máquina.
3. **Caçar a fonte residual:** é aberto, e com risco de prazo. O resultado atual já sustenta a afirmação "a fonte dominante é a acumulação em float; resta uma fonte rara e tardia".

## 2026-10-02 — Diagnóstico dos `.ply` de D4 preparado

Decisão do aluno: seguir com o passo 1 acima, sem sacrificar qualidade por prazo.

**Formato lido no código**, em `VulkanGSTrainer::writePLY`, `vksplat/src/gs_trainer.cpp:1398` em D4:
- cabeçalho ASCII, `binary_little_endian 1.0`;
- 59 `float` por gaussiana (posição, 48 SH, opacidade, 3 escalas, 4 de rotação), 236 bytes por registro;
- registros gravados **na ordem do buffer da GPU**;
- a conversão de escala e opacidade para log/logit é feita na CPU, antes de gravar.

Conferido: 5.940.143 × 236 + cabeçalho = 1.401.875.226 bytes, o tamanho exato das 5 execuções de mesmo `num_splats`.

**Consequência de método:** como a ordem dos registros entra no hash, hashes distintos **não implicam modelos distintos**. O diagnóstico tem de separar dois casos:
- **(a) permutação:** mesmo multiconjunto de gaussianas, gravado em outra ordem;
- **(b) diferença de valor.**

**Script:** `experimentos/diagnosticar_ply_d4.py`. Compara `run000` contra as outras nove execuções e reporta:
- identidade byte a byte;
- teste de permutação, por hash de 64 bits por registro e comparação dos multiconjuntos;
- quando N é igual: quantas gaussianas diferem, em que índices, quais propriedades, e o máximo e o histograma da diferença **em ULP de `float32`**.

Lê por `memmap`, não altera nada e grava um JSON pequeno. É a grandeza secundária "diferenças por parâmetro" do §4, já pré-registrada.

**Testes no Mac,** com `.ply` sintéticos no formato exato do `writePLY`:
- cópia idêntica → identificada como idêntica;
- só a ordem trocada → mesmo multiconjunto;
- 3 gaussianas perturbadas em 1 e 5 ULP → 3 gaussianas, propriedades, índices e ULP corretos;
- registro a mais → N diferente e 1 registro exclusivo.

**Erro meu, encontrado no teste antes de rodar:** a conversão de `float32` para inteiro ordenável tratava errado os negativos. `−0,0` e `+0,0` ficariam a 2³¹ ULP de distância, e o certo é 1. Corrigido para o mapeamento padrão (`~u` nos negativos, `u ^ 0x80000000` nos positivos) e conferido nos casos de borda: zero com sinal, denormais e monotonicidade.

**Executado na Ubuntu em 2026-10-05.** Resultado na entrada seguinte.

## 2026-10-05 — Diagnóstico dos `.ply`: **não é permutação, é deriva de valor em ~99% das gaussianas**; e D3→D4 passa no §5.2

JSON em `dados/D4/diagnostico_ply.json`, commit `1c97ecf`.

### Os modelos diferem de verdade, e as gaussianas estão alinhadas

Referência `run000` contra as outras nove:
- **nenhum par é idêntico, e nenhum par tem o mesmo multiconjunto de registros.** A hipótese de permutação, o caso (a), está descartada;
- nos 4 pares com o mesmo N (`run002`, `005`, `008` e `009`), **de 99,0% a 99,85% das gaussianas diferem** em pelo menos uma propriedade;
- **as gaussianas estão alinhadas por índice**: em `run008`, a maior diferença de posição é de 1,28, 1,33 e 1,30 cm em `x`, `y` e `z`. Desalinhamento daria diferenças na escala da cena. O índice `i` é a mesma gaussiana nas duas execuções, com valores derivados.

### Magnitude da deriva

O histograma de ULP é praticamente idêntico nos 4 pares. Cerca de 0,03% dos valores diferentes ficam em 1 ULP, a mediana em torno de **2²⁰ ULP**, e ~95% abaixo de 2²⁶. Há um pico separado em 2³⁰–2³¹ ULP, com ~5% dos valores. É compatível com valores perto de zero de sinal oposto, já que a distância em ULP explode ao atravessar o zero. **A leitura do pico é inferência**, não verificada valor a valor.

A deriva atinge todos os tipos de parâmetro:
- posição: 5,92 M de valores diferentes;
- SH: 5,8 M;
- opacidade: 5,93 M;
- escala e rotação: apenas **1,40 M e 1,45 M**, cerca de 24%.

A menor fração em escala e rotação é compatível com a hipótese de 2026-10-01, de que o gradiente de cônica é quase todo zerado em D4. Escala e rotação recebem gradiente essencialmente pela covariância. É **compatível**, e não demonstrado.

### Leitura, com a força declarada

Hipótese consistente com os dados: uma perturbação mínima, em algum passo, amplificada pela otimização até alcançar o modelo inteiro. As densificações idênticas até o evento 129, e nos 144 eventos para 5 execuções, só mostram que nenhuma **decisão de limiar** mudou. **Não** mostram bit-identidade dos parâmetros até ali. **O passo em que a divergência começa é desconhecido.** É o fenômeno da H3b ("repetibilidade não implica estabilidade") observado diretamente.

### §5.2 aplicado a D3 → D4

Seed `20260909`, 10.000 reamostragens, critério conjuntivo, exatamente como fixado:

| comparação | Fligner | razão de IQR | IC 95% | critério do §5.2 |
|---|---|---|---|---|
| D3 (N=30) × D4, PSNR, **a pré-registrada** | p = 2,2e−3 | 0,115 | [0,028 – 0,606] | **sustentada** |
| D3 `run020`–`029` (mesmo estrato) × D4, PSNR | p = 1,5e−3 | 0,080 | [0,021 – 0,481] | sustentada |
| D3 × D4, `num_splats` (§4) | p = 7,2e−5 | 0,0012 | [0,000 – 0,006] | sustentada |

**É a primeira transição da escada que passa no critério do §5.2.** Os critérios não se confundem: **H3.4, pela identidade de hash, segue refutada**, e a redução de dispersão, pelo §5.2, é sustentada. O texto reporta os dois, separados.

### Confundidor, registrado porque o resultado é favorável

Em D4, a escala da cônica zera quase todo o gradiente de covariância (entrada de 2026-10-01). Otimizar menos graus de liberdade pode, por si só, deixar a trajetória menos sensível e reduzir a dispersão. **A redução D3→D4 não pode ser atribuída apenas à acumulação inteira enquanto esse confundidor estiver aberto.** O D4b, com a escala da cônica dimensionada pelo regime, deixa de ser opcional.

### Plano de iterações restantes, proposto ao aluno

Decisão do aluno: concluir as iterações antes de escrever. Proposta de data-limite para congelar os dados: **16/out**, a decidir.
1. §5.2 com D4: **feito**, acima.
2. Localizar o início da divergência em D4: hash de parâmetros **e de gradientes inteiros** em passos amostrados, em 2 execuções.
3. Diagnóstico de `.ply` em D3, para comparar a deriva.
4. **D4b**, que exige adendo §11.12 antes de rodar.
5. H4, a comparação com os valores publicados.
6. H3b: executar, ou declarar não executada.
7. Cópia em nuvem dos `.ply`.

### Correspondência entre evento de densificação e passo

Lida no código, `simple_trainer.py:42-44` e `gs_trainer.cpp:829-830` em D4. A densificação ocorre quando `step > refine_start_iter` (500), `step % refine_every == 0` (100) e `step < refine_stop_iter` (15.000). Os 144 eventos são os passos 600, 700, …, 14.900. **O evento 129, em que as densificações de D4 começam a divergir, é o passo 13.500.**

## 2026-10-05 — Rastreador da divergência de D4 preparado (item 2)

`experimentos/rastrear_divergencia_d4.py`. Treina D4 uma vez, com a configuração do `tcc_runner.py`, e depois de cada `train_step` amostrado grava o hash BLAKE2b dos bytes de 21 buffers, agrupados pelo estágio que os escreve. A ordem do pipeline foi lida em `python_bindings.cpp:532-546`: `forward` → gradiente da perda → `backward_optimize` → `post_backward_step`. Os estágios:
- projeção;
- binning;
- forward (a imagem renderizada);
- perda;
- backward (os gradientes inteiros);
- parâmetros, depois do otimizador e da densificação.

O modo `--comparar` dá o primeiro passo amostrado que difere e, nele, o primeiro estágio que difere. **Se a perda coincidir e o backward não, a fonte residual está no backward**, e assim para os outros estágios.

**Amostragem:** passos 0–99; 105–995 de 10 em 10; 1.050–29.950 de 100 em 100; e o 29.999. São 481 amostras, **nenhuma múltipla de 100** fora do 0. Nos passos de densificação e de reset de opacidade os buffers mudam de tamanho, e ler a região nova pode pegar memória não inicializada, que diferiria entre execuções sem significado.

**Verificado antes de escrever:**
- os 21 nomes existem no binding de D4;
- `python_bindings.cpp` é idêntico entre D3 e D4;
- a instrumentação reaproveita a que funcionou em `medir_gradientes_d4.py`, sem tocar no fork, e agora grava no JSON a estratégia usada.

**Testado no Mac, com stand-in e trajetórias sintéticas:**
- o hash é determinístico;
- um erro de acesso a buffer é capturado, e não derruba a execução;
- trajetórias idênticas não mostram diferença;
- divergência que nasce no backward no passo 37 é localizada no passo 37, com os estágios anteriores identificados como idênticos;
- diferença de tamanho no forward é identificada no primeiro passo amostrado depois dela.

Um erro apareceu no teste e era **do stand-in**, não do script: atribuição a uma propriedade só de leitura.

**Limitações:**
- ler um buffer sincroniza a GPU. Não muda a aritmética, mas estas são execuções instrumentadas, **não fazem parte da série medida de D4** e não entram em H3.4;
- a amostragem localiza a divergência num intervalo, e pode ser preciso uma segunda rodada para refinar.

**Primeira tentativa, 2026-10-05: falhou no passo 0, por erro meu.** Saída literal: `TypeError: memoryview: cannot cast view with zeros in shape or strides`, em `hash_buffer`. Algum buffer veio vazio, com uma dimensão zero, no passo 0, e `memoryview(a).cast("B")` não aceita isso. **O stand-in do meu teste nunca teve buffer vazio.** As duas execuções do laço falharam do mesmo modo, segundos depois de começar, e o `--comparar` falhou em seguida por falta do JSON. Nenhum dado foi perdido.

Corrigido: o hash agora é da vista 1-D em `uint8`, que aceita tamanho zero. O `shape` segue registrado, de modo que um buffer vazio numa execução e cheio na outra continua aparecendo como diferença. Testado contra o hash de `tobytes()` com buffers vazios em três formatos, array não contíguo, `int32`, `int64` e `float32`. **Lição: um teste com stand-in precisa incluir os casos degenerados (vazio, não contíguo), não só o caso típico.**

Fato útil revelado pela tentativa: `instrumentacao ativa via: patch de metodo em VkSplat.train_step`. A estratégia (a) funciona no binding pybind11 real. É provável que tenha sido ela também na medição de gradientes de 2026-09-23, **mas aquela execução não a registrou, e isso continua não estabelecido.**

## 2026-10-06 — Rastreamento de D4: **estado bit-idêntico em todos os 21 buffers até o passo 14.050**

Segunda tentativa, executada na Ubuntu: 2 execuções instrumentadas de D4, 481 amostras e 30.000 chamadas cada. A rep01 terminou com PSNR 27,01, dentro da faixa da série. Saída literal do `--comparar`:

```
amostras em comum: 481  (A=481, B=481)
ULTIMO passo amostrado com TUDO identico: 14050
PRIMEIRO passo amostrado com diferenca : 14150
  [os 20 buffers com conteúdo diferem, dos seis estágios]
  primeiro estagio que difere: projecao
```

**Os JSON de trajetória ainda não estão no repositório**, em `dados/D4/`. A leitura abaixo vem da saída do terminal colada pelo aluno.

### O resultado

As duas execuções ficaram **bit-idênticas em todos os 21 buffers**, nos seis estágios do pipeline, **em todas as amostras do passo 0 ao 14.050**:
- os gradientes inteiros do backward;
- a imagem renderizada e o gradiente da perda;
- todos os parâmetros, depois do otimizador e da densificação.

Não há verificação nos passos não amostrados. Mas um estado bit-idêntico no passo 14.050, com 47% do treino percorrido, só é compatível com trajetórias idênticas até ali, salvo uma reconvergência exata, que é implausível.

**Contraste com D3,** pelos dados de `dados/gradientes/` (2026-09-23): no **passo 0** de D3, apenas 71 dos 137 campos estatísticos dos gradientes coincidem entre as três repetições. **Em D3 a divergência nasce no primeiro backward. Em D4, o estado inteiro permanece idêntico por mais de 14 mil passos.** É a evidência mais direta do trabalho de que a acumulação em `float32` é a fonte imediata e dominante, e de que a acumulação inteira a elimina.

### O que não se sabe

No passo 14.150, **todos** os estágios diferem, a começar pela projeção. Como a projeção do passo 14.150 só lê os parâmetros deixados pelo passo 14.149, **a divergência nasceu em algum passo de 14.051 a 14.149**. Nessa amostragem, um passo basta para a diferença se espalhar por todo o pipeline, então nem o passo nem o estágio de origem são identificáveis.

A janela contém **um** passo de densificação, o 14.100. É candidato natural, e nada além disso: são 99 passos, e só um deles é de densificação.

### Escrutínio, porque o resultado é favorável

- **Efeito da instrumentação.** Estas execuções sincronizam a GPU 481 vezes. Não muda a aritmética, mas pode mudar temporização e, se a fonte residual depender de temporização, mudar onde ela aparece. Aqui a divergência começou depois de 14.050. Na série medida, as densificações já diferiam no evento 129, o passo 13.500. É consistente com uma fonte rara de início variável, **e** é consistente com interferência da instrumentação. Não se distingue com este dado.
- **Um único par.** É uma observação do início da divergência, não a distribuição dele.

### Próximo: modo denso, para localizar o passo exato

Como o início varia de par para par, adensar só a janela 14.050–14.150 não serve. Acrescentei ao rastreador o `--modo denso`: **todo passo**, com 5 buffers válidos inclusive nos passos de densificação. São `pixel_state`, `n_contributors`, `v_pixel_state`, `xyz_ws` e `opacities`, cerca de 110 MB por passo no fim do treino. O `--comparar` lê do próprio JSON a lista de estágios gravados e informa a janela de origem e se ela contém passo de densificação. O critério de densificação vem do código: `500 < passo < 15000` e `passo % 100 == 0`.

**Leitura pré-definida, antes de rodar:**
- Se o passo de origem `S` for de densificação, isso é forte evidência contra o acaso, porque só 1 em cada 100 passos é de densificação.
- Se não for, e a imagem e a perda de `S` coincidirem enquanto os parâmetros divergem, a fonte está no backward. A inferência é por eliminação: o otimizador recebe entradas idênticas, exceto pelos gradientes, e o perfil de instruções mostrou zero atômicos no `.spv` dele.
- **Limitação:** o modo leve não grava `v_*`, então essa última conclusão é inferência e não observação.

Testado com trajetórias sintéticas: origem num passo de densificação, origem fora dele, e conjuntos de buffers incompatíveis, caso em que o script aborta.

**Erro meu de estimativa (2026-10-06).** Anunciei ~45 min por execução no modo denso. O aluno observou **~1 it/s**, o que dá ~8,3 h por execução e ~17 h pelo par. Estimei pelo volume de dados (~110 MB por passo a GB/s) e não medi o custo por amostra. O número observado indica **~1 s por amostra, independente do volume**. É coerente com a rodada completa: 481 amostras a ~1 s somam uns 8 minutos sobre o treino, e passaram despercebidos. Lição: medir o custo por amostra antes de anunciar prazo de execução instrumentada. Decisão a tomar: deixar o par terminar (recomendado), ou interromper e redesenhar com o modo denso restrito a uma faixa, o que exige um par novo.

**Mecanismo, lido no código depois de o aluno notar a GPU ociosa.** Cada leitura de buffer é serial:
1. `copyFromDevice` (`buffer.cpp:342-368`) grava uma cópia do buffer para a área de staging e **espera a GPU terminar** (fence no `HOST_GUARD`); depois faz `memcpy` para a RAM;
2. `buffer_to_array` (`python_bindings.cpp:21-73`) copia para o array numpy;
3. o meu `np.ascontiguousarray` copia de novo `opacities`, que é uma coluna de `scales_opacs`, portanto não contígua;
4. o BLAKE2b roda numa única thread.

São 5 buffers por passo. A GPU fica ociosa quase todo o tempo, esperando a CPU, o que explica as ventoinhas paradas. **A divisão do custo entre as etapas não foi medida.** É explicação por leitura de código, compatível com o ~1 s observado. Ganhos para uma rodada futura: hash em paralelo, sem a cópia de contiguidade, e com uma única leitura de `scales_opacs`. **Não aplicados**, para não mudar o instrumento no meio de um par.

**Ameaça de falso positivo, verificada e afastada.** A preocupação: se o hash incluísse a folga de alocação, memória não inicializada poderia diferir entre execuções e produzir uma "divergência" falsa justo depois de uma densificação, a hipótese que o modo denso testa. O código afasta isso. `_VulkanBuffer` separa `allocSize` (alocação) de `size` (tamanho lógico, ajustado exatamente para o pedido em `buffer.cpp:193` e `:233`), e o `copyFromDevice` copia `size` (`:345`, `:358`). Na ADC o tamanho pedido para os parâmetros é o número de gaussianas ativas (`gs_trainer.cpp:726-728`). Resta a condição de que tudo dentro do tamanho lógico esteja escrito, o que vale para os parâmetros depois da densificação. **Salvaguarda adicional, a aplicar na leitura do resultado:** uma diferença nos parâmetros no passo `S` só é aceita como divergência real se a imagem renderizada (`pixel_state`) também divergir em `S+1`.

## 2026-10-07 — Par denso de D4: primeira diferença no **forward do passo 16.165**, fora da densificação

JSONs em `dados/D4/trajetoria_denso_rep0{0,1}.json`, commit `5d4435b`. Conferido antes de comparar que são duas execuções distintas, porque os arquivos têm o mesmo tamanho (16.905.920 bytes):
- hashes de arquivo diferentes;
- `rep` 0 e 1;
- rodadas em sequência, de 2026-10-06 04:40Z a 13:19Z e de 13:19Z a 21:50Z, ~8,6 h cada;
- 30.000 amostras e 30.000 chamadas cada, commit de D4, estratégia (a).

O tamanho igual é efeito do formato, de hashes de largura fixa.

**Reconferência da rodada completa pelos próprios JSON** (`trajetoria_rep0{0,1}.json`, `2f71697`): bate com o terminal, idêntico até 14.050 e diferente a partir da projeção em 14.150. O buffer vazio que derrubou a primeira tentativa era o **`ssim_map`**.

### Resultado do par denso

Saída literal do `--comparar`:

```
ULTIMO passo amostrado com TUDO identico: 16164
PRIMEIRO passo amostrado com diferenca : 16165
  forward pixel_state, forward n_contributors, perda v_pixel_state, parametros xyz_ws, parametros opacities
  primeiro estagio que difere: forward
```

**Demonstrado:**
- todos os buffers monitorados (imagem, contribuições por pixel, gradiente da perda, posições, opacidades) ficaram idênticos **em todo passo de 0 a 16.164**;
- no passo 16.165, a primeira diferença está no forward;
- **a densificação está descartada como fonte para este par.** Ela termina no passo 14.900 (`refine_stop_iter = 15000`), e o passo 16.165 também não é de reset de opacidade, que ocorre em múltiplos de 3.000.

**Isto refuta a candidata que eu tinha apontado em 2026-10-06**, a densificação do passo 14.100. Ela era apenas candidata, e foi apresentada assim.

**Não demonstrado, e erro meu de desenho:** a saída da ferramenta dizia "o passo 16.165 é o de origem". **O modo leve não sustenta isso**, porque não monitora SH, escalas e rotações. Há duas explicações compatíveis:
- **(a)** o forward do passo 16.165 produz resultados diferentes a partir de entradas idênticas;
- **(b)** SH, escala ou rotação de alguma gaussiana divergiram antes, sem ter chegado ainda aos buffers monitorados.

A diferença em `n_contributors`, que depende da geometria e da ordem, e não da cor, restringe (b) a **escala ou rotação**. A mensagem da ferramenta foi corrigida: agora diz "primeiro passo em que se **observa** diferença" e imprime a ressalva dos parâmetros não monitorados.

### Inventário de atômicos no caminho ativo de D4

Contagem em todos os `.slang` e nos `.comp` do radix sort, em D4. Fora as três variantes de backward, o `morton_sort` (desligado em D3) e o `mcmc` (não usado na ADC), sobram dois:
- **`sum.slang:47`**: `InterlockedAdd` **inteiro** de contagem, usado só na densificação (`gs_trainer.cpp:852-853, 952`), para contar quantas gaussianas duplicar, dividir ou manter. Não roda depois do passo 15.000;
- **radix sort**: `upsweep.comp:57,66` e `downsweep.comp:137,200`, atômicos **inteiros** de histograma. No `downsweep`, cada posição é indexada por subgrupo (`gl_NumSubgroups * radix + subgroupIndex`) e escrita só pelo representante do subgrupo; a posição dentro do subgrupo vem de soma prefixada por *ballot*. É consistente com a auditoria de 2026-09-02: ordenação estável dada a mesma entrada.

**Leitura, como inferência:** no caminho ativo de D4 não resta acumulação atômica não-associativa. Se isso estiver certo, **a fonte residual não é atômica**. Os candidatos seriam condição de corrida, leitura de memória não inicializada ou comportamento do hardware. Não demonstrado.

### Próximo teste, preparado: determinismo por estágio em estado fixo

`experimentos/testar_estagios.py`. Em 7 pontos do treino (1.050, 5.050, 10.050, 14.050, 16.050, 20.050 e 29.950, nenhum múltiplo de 100), com os parâmetros congelados no estado daquele passo, repete K=20 vezes `forward()` → `compute_pixel_loss_grad()` → `rasterize_backward()`, e conta os hashes distintos de cada buffer.

Nenhuma dessas chamadas altera parâmetros ou momentos. O `rasterize_backward` só escreve nos `v_*`, que zera no início. Cada função abre o próprio `DEVICE_GUARD` (`gs_renderer.cpp:91, 171, 204, 322`; `gs_trainer.cpp:649`), e o `DeviceGuard` é aninhável (`gs_pipeline.h:207-240`). Isso foi verificado no código antes de escrever.

**Leitura pré-definida:**
- **imagem variando:** o forward é não-determinístico por si só, e a hipótese (a) fica diretamente observada;
- **`v_*` variando em D4:** a acumulação inteira não é determinística no RADV, o que contradiria o desenho de D4;
- **tudo idêntico:** (a) cai, e a fonte fica no otimizador ou na interação entre passos.

**Controle positivo obrigatório: o mesmo teste em D3.** Lá o backward usa `InterlockedAddF32`, e os `v_*` **têm** de variar. Se D3 também der "determinístico", o teste é insensível e o resultado de D4 não vale nada.

Testado com stand-ins: um módulo determinístico dá 1 hash distinto em tudo, e um módulo com backward não-determinístico dá 20 distintos só no buffer afetado. Custo previsto: um treino por degrau, mais 7 × 20 repetições. **Não arrisco nova estimativa de tempo antes de medir:** a de 2026-10-06 errou por um fator de ~11.

## 2026-10-13 — Teste de estágios: **leitura pré-definida corrigida antes de rodar**, e tempo por repetição instrumentado

Nenhuma execução entre 2026-10-07 e hoje. O último commit continua `5d4435b`, e `origin/main` está no mesmo ponto. O `testar_estagios.py` segue **não versionado**, e portanto não chega à Ubuntu por `git pull`.

### Correção da leitura pré-definida de 2026-10-07

A leitura dizia "**tudo idêntico: (a) cai**". **Estava errada, e no sentido favorável à tese.** Ela só valeria se o forward fosse frequentemente não-determinístico, e os dados indicam o contrário:
- o par completo diverge por volta do passo 14.100, e o par denso no 16.165;
- como estimativa grosseira, tirada apenas desses dois inícios, isso dá uma taxa da ordem de **1 evento a cada ~3·10⁴ passos por execução**;
- com K=20 em 7 pontos são 140 forwards, e a chance de observar um evento a essa taxa fica em **~0,5%**.

O teste daria "determinístico" mesmo com (a) verdadeira. **O controle positivo em D3 não cobre esse buraco:** ele mostra que o teste detecta não-determinismo ubíquo, não um evento raro.

**Leitura corrigida, fixada hoje, antes de qualquer execução:**
- **buffer com mais de um hash distinto:** evidência direta de não-determinismo daquele estágio a partir de entradas idênticas. Esta parte não muda;
- **tudo idêntico em K repetições:** **não refuta (a).** Refuta apenas um estágio *frequentemente* não-determinístico naquele estado. Reporta-se o limite superior de 95% da taxa por repetição, `1 − 0,05^(1/K)` (≈ 3/K; 0,139 para K=20). Ele pressupõe **tentativas independentes e taxa constante, o que não foi verificado**;
- **D3 sem variação nos `v_*`:** o teste é insensível, e D4 não vale nada. Esta parte também não muda.

Esta leitura não está no pré-registro: é diagnóstico exploratório, e a correção não é desvio do §11. Fica registrada aqui com data porque **é anterior aos dados**.

**Ressalva que se mantém:** cada leitura de buffer sincroniza a GPU entre um estágio e outro. Se a fonte residual for uma condição de corrida dependente de temporização, o teste pode suprimi-la.

### Mudanças no script

- **Tempo por repetição:** total, chamadas (forward, perda e backward) e leitura com hash, gravados no JSON (`tempo.rep_s`, `chamadas_s`, `leitura_hash_s`, `mediana_rep_s`) e impressos ao fim de cada ponto. **A divisão não separa GPU de CPU.** Não verifiquei se o `DeviceGuard` espera a GPU ao sair, e o `copyFromDevice` espera a fence, então parte do tempo de GPU pode cair na conta da leitura;
- `--pontos` e `--k` passam a ser argumentos, com os mesmos padrões de antes (7 pontos, K=20). A validação rejeita lista vazia, repetida, negativa ou com múltiplo de 100, e K < 2;
- **multiplicidades** de cada hash e o limite superior de 95% gravados por buffer;
- o JSON é **regravado ao fim de cada ponto**, com o campo `completo`, de modo que um aborto não perde os pontos já medidos.

Assinaturas reconferidas no fork, em D4: `forward()` (`python_bindings.cpp:463`), `compute_pixel_loss_grad(size_t)` (`:483`), `rasterize_backward()` (`:455`) e `train_step(size_t, int)` (`:532`), chamado como `module.train_step(image_idx, step)` em `simple_trainer.py:213`.

### Testes no Mac, com stand-ins

Os stand-ins são um fork falso em repositório git, um `vksplat` falso e um `simple_trainer` falso.
- Hash bate com `tobytes()` em buffer vazio 1-D, vazio 2-D, não contíguo e `int64`.
- Módulo determinístico: tudo 1, saída 0.
- Uma única repetição divergente no forward: `pixel_state` e `v_pixel_state` com multiplicidades [19, 1], o resto igual a 1. É o caso raro que importa.
- Backward não-determinístico: 20 distintos só em `v_xy_vs`.
- Buffers vazios (`n_contributors` e `v_inv_cov_vs_opacity`) e `v_rgb` não contíguo: rodam sem erro.
- Treino curto demais: aborta com saída 2, deixando JSON parcial com `completo: false` e 1 ponto.
- SHA errado e árvore suja: abortam com saída 1.
- Os seis argumentos inválidos são rejeitados com saída 2.
- Padrão com 30.000 passos simulados: 7 pontos, K=20, `completo: true`.

**Os stand-ins não medem custo.** O tempo real só sai na Ubuntu.

### Decisão sobre K (item 3), tomada pelo aluno em 2026-10-13, antes dos dados

O problema de poder: aumentar K tem limite. A uma taxa uniforme de ~1/(3·10⁴), detectar com 95% exigiria ~9·10⁴ repetições, o que é inviável. Um K grande só tem poder se a taxa **depender do estado**, crescendo tarde no treino. Por isso os pontos tardios são os candidatos.

**Fase 1:** D4 e D3 com os padrões, 7 pontos e K=20. Ela entrega três coisas:
- o controle positivo;
- a checagem de um forward frequentemente não-determinístico;
- o custo medido por repetição em cada ponto.

**Fase 2, regra fixada agora:**
- **Condição:** roda só se, na fase 1, **D3** tiver mais de um hash distinto em algum `v_*` **e D4** tiver todos os buffers em 1 nos 7 pontos. Se D4 variar na fase 1, a observação já é direta, e a fase 2 não roda;
- **degrau e pontos:** D4, nos passos **16.050 e 29.950**, numa única execução nova;
- **orçamento:** **3 h de repetições no total**, com o mesmo K nos dois pontos. O treino de ~15 min fica fora da conta;
- **K**, um só para os dois pontos, porque o script aplica um único `--k` = `floor(10800 s / (c₁₆₀₅₀ + c₂₉₉₅₀))`. Aqui `c` é a mediana de segundos por repetição (`tempo.mediana_rep_s`) **do mesmo ponto na fase 1 de D4**. *(Redação inicial, corrigida minutos depois na mesma sessão e antes de qualquer dado: dizia "K por ponto = `floor(5400 s / c)`", o que o script não suporta numa única execução.)*;
- **leitura:** a mesma da fase 1. Mais de um hash é observação direta; tudo idêntico é reportado como limite superior `1 − 0,05^(1/K)`.

**Declarado antes de rodar:** nem com 3 h se alcança uma taxa uniforme de ~1/(3·10⁴). A fase 2 só tem poder contra uma taxa que cresça com o estado do treino.

Comentário do aluno ao decidir: *"Vamos utilizar o tempo de máquina que for necessário para um bom projeto."*

## 2026-10-14 — Fase 1 do teste de estágios **travou no passo 1.050**: a causa provável é um erro meu de uso da API do fork

### Observado, saída literal colada pelo aluno

A primeira execução foi a de D4. O treino seguiu até o passo 1.050, imprimiu `[estagios] passo 1050: 20 repeticoes ...` e não imprimiu mais nada. Diagnóstico do aluno às 04:37 de 2026-10-14:
- `PID=35974`, `ELAPSED 09:26:27`, `STAT Rl+`, `%CPU 100`, `RSS 1407392`, `WCHAN -`;
- no `top -H`, uma única thread a 99,9% de CPU e as outras 33 dormindo;
- `gpu_busy_percent` = **0**;
- memória: 10 GiB disponíveis e swap praticamente sem uso. **Não é falta de memória.**

O `dmesg` não chegou a ser visto, porque ficou parado no pedido de senha do `sudo`.

O perfil é de uma thread girando em espaço de usuário com a GPU ociosa. Nenhum JSON foi gravado, porque o primeiro ponto não terminou.

### Mecanismo provável, lido no fork em D4. **Hipótese, a confirmar pelo stack**

1. `config.h:6` define `ENABLE_ASSERTION 0`. Com isso, `_THROW_ERROR` é **no-op** (`config.h:44`): as checagens do fork não lançam nada, seguem em frente.
2. `writeTimestamp` (`gs_pipeline.cpp:602-618`) deveria recusar-se a rodar sem lote de comandos aberto (`:603-604`). Como a checagem é no-op, ele grava `vkCmdWriteTimestamp` num command buffer **fora do estado de gravação** e incrementa `timestampNumWritten`.
3. `executeComputeSSIMGradient` cria o timer (`gs_trainer.cpp:647`) **antes** do `DEVICE_GUARD` (`:649`). O mesmo vale para `executeRasterizeBackward`: o timer está em `gs_renderer.cpp:316` e o guard em `:321`. No treino normal isso é inofensivo, porque as duas funções rodam dentro do guard externo do `train_step` (`python_bindings.cpp:538`). **No meu teste elas são chamadas do Python sem guard externo** (`python_bindings.cpp:455` e `:483` não abrem guard). Só `forward()` abre (`:464`).
4. Em seguida o guard abre o lote. O `beginCommandBatch` reinicia o command buffer e zera o pool de consultas (`gs_pipeline.cpp:520-523`). O timestamp gravado fora do lote se perde, mas o contador continua dizendo que ele existe.
5. No fim do lote, `endCommandBatch` lê `timestampNumWritten` consultas com `VK_QUERY_RESULT_WAIT_BIT` (`gs_pipeline.cpp:584-589`). A consulta 0 foi zerada e nunca escrita, então nunca fica disponível. **A espera não termina.**

**Previsões que testam a hipótese:**
- o stack da thread presa tem `vkGetQueryPoolResults` dentro de `endCommandBatch`, chamado pelo destrutor do `DeviceGuard` em `executeComputeSSIMGradient`;
- o `dmesg` **não** mostra reset da GPU. Não houve travamento de GPU: ela terminou o trabalho e ficou ociosa.

Que o RADV implemente essa espera girando a CPU é inferência minha, compatível com 100% de CPU e `WCHAN -`, e não foi verificada no código do Mesa.

### Erro meu

Em 2026-10-07 registrei que "cada função abre o próprio `DEVICE_GUARD`". Conferi que o guard **existe**, e não o que roda **antes** dele. E os stand-ins não modelam o estado de lote do binding real, então nenhum teste no Mac podia pegar isto. **Lição:** um stand-in testa a lógica do script, não as pré-condições da API real. Chamar o binding numa ordem que o próprio fork nunca usa exige ler a função inteira, e não só procurar o guard.

### O que não é afetado

O rastreador (2026-10-05/06) só lia buffers depois de `train_step` retornar e nunca chamava estágios isolados. Os dados de trajetória não passam por este caminho.

### Pendente

- confirmar pelo stack e pelo `dmesg`. **A saída ainda não veio**, e o redesenho abaixo parte da hipótese;
- encerrar o processo.

### Redesenho: decisão do aluno pela opção B, binding auxiliar

Opções apresentadas:
- **A:** só o forward, sem tocar no fork, perdendo o controle positivo;
- **B:** binding auxiliar, mantendo o desenho completo.

O aluno escolheu **B**.

**Patch, `experimentos/patches/estagios_bindings.patch`, só no binding.** Acrescenta a `python_bindings.cpp` dois métodos, `compute_pixel_loss_grad_guarded` e `rasterize_backward_guarded`. Cada um abre um `DeviceGuard` e chama o método original, o mesmo padrão de `forward()` (`python_bindings.cpp:463-468`). Conferido no Mac:
- `python_bindings.cpp` é idêntico entre D3 e D4;
- o patch aplica limpo nas duas tags;
- comparada à tag, a árvore inteira de `vksplat/` difere **apenas** em `python_bindings.cpp`. Nenhum `.slang` nem `.spv` muda.

**Não compilado no Mac**, que não tem o ambiente Vulkan. A primeira compilação será na Ubuntu.

**Por que o patch corrige o problema, pelo código:**
- com o lote já aberto pelo guard externo, o timer criado antes do `DEVICE_GUARD` interno grava dentro do lote, como acontece no `train_step`;
- o `~DeviceGuard` chama `endCommandBatch(true)` (`gs_pipeline.h:47`, `:229`), que espera a fence. Cada estágio é síncrono, e o tempo de "chamadas" passa a incluir a GPU, o que corrige a ressalva de 2026-10-13 sobre a divisão do tempo;
- a cópia da imagem de referência para a GPU (`gs_trainer.cpp:636-641`) passa por `HOST_GUARD`, que fecha e reabre o lote com o mecanismo de marcadores do próprio fork. É o mesmo caminho do treino normal, porque o cache de imagens fica na CPU.

**Diferença declarada em relação ao treino:** no `train_step`, forward, perda e backward vão num único lote. Aqui cada estágio é submetido e sincronizado separadamente. A aritmética é a mesma, a temporização não. A ressalva de 2026-10-13 sobre suprimir uma condição de corrida vale ainda mais.

**Mudanças no script.** Antes de treinar, ele exige:
- `HEAD^` igual à tag do degrau;
- diff `HEAD^..HEAD` só em `python_bindings.cpp`, com as linhas alteradas idênticas às do patch;
- árvore limpa;
- módulo carregado com os dois métodos. Isso pega um binário antigo: o `.so` não é versionado e o `checkout` não o troca, a mesma armadilha do §3.2.

O JSON grava `base_commit`, `vksplat_commit`, o SHA-256 do patch e o caminho e o `mtime` do módulo.

**Testes no Mac.** Desta vez o stand-in **modela a pré-condição do lote**: os métodos sem guard falham fora de lote. O fork falso contém o `python_bindings.cpp` real de D4, com o patch commitado. Resultados:
- o stand-in falha ao chamar `compute_pixel_loss_grad` fora de lote, e funciona com `_guarded`;
- determinístico: tudo 1;
- uma repetição divergente no forward: multiplicidades [19, 1] em `pixel_state` e `v_pixel_state`;
- backward não-determinístico: 20 em `v_xy_vs`;
- buffers vazios e não contíguos: rodam;
- aborto: saída 2, com JSON parcial;
- saída 1, **antes de treinar**, em cada um destes casos: tag sem patch; árvore suja; commit que altera um arquivo a mais; diff diferente do patch; dois commits sobre a tag; módulo sem os métodos.

**Erro de stand-in, corrigido:** na primeira rodada, o caso "raro" não foi detectado porque o `train_step` falso também chama `forward` e o disparo caiu no treino. O erro era do teste, não do script. Refeito com o disparo na 7ª repetição do passo 105: detectado.

## 2026-10-14 — Teste de estágios, fase 1: **em D3 o não-determinismo está todo no backward**; em D4 nada varia em 140 repetições; a condição da fase 2 foi satisfeita

JSONs em `pivo-reprodutibilidade-3dgs/dados/estagios/estagios_D{3,4}.json`, ainda não commitados. SHA-256 dos arquivos:
- D3: `9d291cb9…`;
- D4: `b24aa2a4…`.

As tabelas saíram no terminal e foram coladas pelo aluno.

### Integridade, conferida antes de ler os resultados

- `base_commit` igual às tags: D3 `d222c47…`, D4 `22560858…`;
- commits de diagnóstico `9e78e28…` (D3) e `48324989…` (D4);
- SHA-256 do patch igual ao do arquivo versionado, `f44cd7c9…`;
- `mtime` do módulo 0,5 a 0,6 s antes do início de cada execução, ou seja, recompilado imediatamente antes. Não houve binário antigo;
- `completo: true`, 7 pontos e K=20 nos dois;
- as mesmas imagens sorteadas nos mesmos passos dos dois degraus (68, 81, 77, 91, 60, 38, 41);
- D4 termina com **5.940.143 gaussianas, o valor modal da série de D4**, atingido por 5 das 10 execuções. D3 termina com 5.808.817, perto da mediana de D3. É evidência independente de que cada execução carregou os shaders do seu degrau.

**A trava de 2026-10-13/14 fica corroborada de forma indireta.** A única mudança foi o guard, e com ele as mesmas chamadas rodaram 280 vezes sem travar. **O stack da execução travada não foi capturado.** A causa continua inferida pela leitura do código e corroborada pela correção; não foi observada.

### Resultado

| | `pixel_state` | `n_contributors` | `v_pixel_state` | `v_xy_vs` | `v_inv_cov_vs_opacity` | `v_rgb` |
|---|---|---|---|---|---|---|
| D3, 7 pontos | 1 | 1 | 1 | **20** | **20** | **20** |
| D4, 7 pontos | 1 | 1 | 1 | 1 | 1 | 1 |

Em D3, as multiplicidades dos `v_*` são `[1]×20` em todos os pontos: **cada uma das 140 repetições do backward produziu um gradiente diferente**, a partir de entradas idênticas.

### Leitura, pela regra fixada em 2026-10-13

- **Controle positivo, D3: aprovado.** O teste detecta não-determinismo no backward, e o detecta em toda repetição.
- **D3, localização:** forward e perda deram 1 hash em 140 repetições, e o backward deu 140 hashes distintos em 140. **No estado fixo, o não-determinismo de D3 está inteiro no backward.** É a localização por estágio, observada diretamente, que o mecanismo do TCC prevê: o backward é onde estão os atômicos de `float`.
- **D4:** zero eventos em 140 repetições, em todos os estágios. Por ponto, o limite superior de 95% da taxa por repetição é 0,139. **Isto não refuta (a)**, porque refuta só um estágio *frequentemente* não-determinístico. Agregar os 7 pontos daria um limite menor, mas supõe taxa constante entre estados, o que não foi fixado nem verificado, e por isso não se reporta como resultado.
- **Contraste D3 × D4 no backward:** 140 de 140 contra 0 de 140, com instrumentação idêntica. É a evidência no nível de estágio de que a acumulação inteira elimina o não-determinismo do backward. **Escrutínio, porque favorece a tese:**
  - **buffers zerados dariam hash constante de forma trivial.** O JSON não grava os valores, então isso não foi verificado diretamente. Mas os mesmos buffers alimentam o otimizador, e D4 treina até PSNR ≈ 27 na série. Gradiente identicamente nulo não treinaria. É exclusão indireta;
  - **a sincronização é pesada e igual nos dois degraus** (ver tempo, abaixo). Uma corrida dependente de temporização pode estar suprimida nos dois. Isso não afeta o contraste, que é sobre o atômico de `float`, mas limita o que D4 diz sobre a fonte residual.

### Tempo, medido

- Mediana por repetição, de 0,28 s (N ≈ 0,33 M) a **1,59 s** (N ≈ 5,9 M, em D4).
- **~97% do tempo é leitura com hash na CPU.** Chamadas (GPU) ~0,04 s contra leitura ~1,54 s nos pontos tardios. A GPU fica ociosa a maior parte do tempo instrumentado, o que **reforça a ressalva de temporização**.
- Duração: D4 levou 19 min e D3 20 min de ponta a ponta, treino incluído.

### Fase 2: condição satisfeita, K calculado pela regra

A condição era D3 com mais de um hash em algum `v_*` e D4 com tudo igual a 1 nos 7 pontos. As duas partes valem.

`K = floor(10800 / (c₁₆₀₅₀ + c₂₉₉₅₀)) = floor(10800 / (1,5864 + 1,5836)) = floor(10800 / 3,1700) =` **3406**. Os `c` vêm de `tempo.mediana_rep_s` da fase 1 de D4.

- Limite superior de 95%, se não houver eventos: **8,8·10⁻⁴ por repetição, por ponto**.
- Custo estimado **a partir do custo medido**: 2 × 3406 × ~1,585 s ≈ 3,0 h de repetições, mais ~16 min de treino, ou **~3 h 20 min**.

Como declarado antes de rodar: nem assim se alcança uma taxa uniforme da ordem de 3·10⁻⁵ por passo.

**Avaliação e contadores da execução de D4, do `D4.log` enviado pelo aluno** (não versionado):
- **PSNR 27,00, SSIM 0,847, LPIPS-Alex 0,100** (VGG 0,131). Coincide com a série de D4 (mediana 26,998, SSIM 0,8471, LPIPS-Alex 0,0998) e não com D3. Os valores da execução de D3 são PSNR 27,35, SSIM 0,864 e LPIPS-Alex 0,076. É a terceira confirmação independente de que cada execução rodou o seu degrau.
- **Contadores dos próprios timers do fork**, impressos no fim do treino:
  - `ProjectionForward`, `RasterizeForward`, `ComputeSSIMGradient` e `RasterizeBackward`: **30.140** cada, ou seja 30.000 do treino mais 7 × 20 do teste;
  - `FusedProjectionBackwardOptimizerStep` e `DefaultPostBackward`: **exatamente 30.000**.

  **As repetições executaram os três estágios e nunca chamaram o otimizador nem o pós-backward.** Até aqui isso vinha da leitura do código. Agora está confirmado pela instrumentação do próprio fork.
- `_Where` = 288 e `_Sum` = 432, isto é 2 × 144 e 3 × 144: são os 144 eventos de densificação.
- Nenhuma ocorrência de `Timed out` nem de `commandBatchInProgress changed`.

## 2026-10-14 — Fase 2 em execução; **o alarme de "congelamento" era o silêncio esperado do script**

A fase 2 foi iniciada com o comando registrado. O aluno relatou que o terminal parecia congelado depois de `[estagios] passo 16050: 3406 repeticoes ...`, com o treino em 53%. O relato inicial falava em "3046", **mas a linha literal do log diz 3406**: o K é o registrado e não há desvio.

**Causa da aparência de travamento, omissão minha de desenho:** o script não imprime nada durante as K repetições de um ponto. Com K=3406 e o custo medido de ~1,586 s por repetição, são ~90 min sem saída por ponto.

**Evidência de que está rodando, saída literal das 17:05:51:**
- processo `97254`, `ELAPSED 01:13:46`, `STAT Rl+`, 100% de CPU;
- última escrita no log às 15:59:07, ou seja **66,7 min** antes, abaixo dos ~90 min esperados para o ponto;
- `gpu_busy_percent` em 200 amostras ao longo de ~10 s: **77 acima de zero**, com valores até 53. No travamento de 2026-10-13/14 estava em 0. A GPU recebe trabalho periodicamente, como esperado das rajadas de cada repetição;
- RSS de 1.411.492 KB, e 1.411.516 KB 60 s depois. **Sem vazamento.**

**Previsão a partir do custo medido:**
- passo 16.050 termina por volta das 17:29;
- ~8 min de treino até o passo 29.950;
- passo 29.950 termina por volta das 19:07;
- avaliação e relatório por volta das 19:10.

**A corrigir depois desta execução, não durante:** imprimir uma linha de progresso a cada 100 repetições. Não se altera o instrumento no meio da execução.

## 2026-10-14 — Fase 2: **um evento em 3.406 repetições, só em `v_rgb`, no passo 16.050**

JSON em `pivo-reprodutibilidade-3dgs/dados/estagios/estagios_D4_fase2.json`, com SHA-256 `b815bd17…`, ainda não commitado. A tabela final foi colada pelo aluno.

### Integridade

- `base_commit` = D4, commit de diagnóstico `48324989…` (o mesmo da fase 1), SHA do patch `f44cd7c9…`;
- módulo recompilado 0,4 s antes do início;
- `completo: true`, K=3406, pontos 16.050 e 29.950;
- de 18:52Z a 22:13Z, ou seja **3 h 21 min**, contra os ~3 h 20 min previstos pelo custo medido;
- avaliação PSNR 27,00, SSIM 0,847, LPIPS-Alex 0,100, compatível com D4;
- mediana de 1,637 s por repetição no 16.050 e 1,627 s no 29.950. Máximo de 1,681 s e **nenhuma repetição acima de 1,5× a mediana**: não há anomalia de tempo.

### Resultado

| passo | `pixel_state` | `n_contributors` | `v_pixel_state` | `v_xy_vs` | `v_inv_cov_vs_opacity` | `v_rgb` |
|---|---|---|---|---|---|---|
| 16.050 | 1 | 1 | 1 | 1 | 1 | **2, multiplicidades [3405, 1]** |
| 29.950 | 1 | 1 | 1 | 1 | 1 | 1 |

**Uma única repetição** do passo 16.050 produziu um `v_rgb` diferente das outras 3.405. Nela, todos os outros buffers coincidiram com as demais repetições. As multiplicidades [3405, 1] excluem uma mudança de estado no meio da série, que daria duas classes grandes. É um evento isolado. **O JSON não registra em qual repetição ocorreu**, porque grava contagens e não a sequência de hashes.

### Leitura pela regra fixada, e o que ela não previu

A regra de 2026-10-13 diz que mais de um hash distinto é evidência direta de não-determinismo daquele estágio a partir de entradas idênticas. **O evento satisfaz a regra.** Duas qualificações, que a regra não antecipou e que restringem a leitura, não a ampliam:

1. **"Entradas idênticas" só foram verificadas nos buffers com hash.** O backward também lê intermediários da projeção e da ordenação (`xy_vs`, `inv_cov_vs_opacity`, `rgb`, `sorted_gauss_idx`, `tile_ranges`; `gs_renderer.cpp:348-356`), que o forward recalcula a cada repetição e que não têm hash. Atenua: nessa repetição a imagem, as contribuições e o gradiente da perda coincidiram. E pela equação do backward, `v_rgb` depende de α, T e `v_pixel_state`, não de `rgb`. Uma mudança em α ou T que alterasse `v_rgb` sem tocar `v_xy_vs` nem a imagem é improvável, mas não está excluída.
2. **A cadeia de medição faz parte da observação.** Uma falha transitória na leitura, que passa por cópia GPU → staging → RAM, `memcpy`, cópia numpy e hash, cerca de 71 MB por leitura de `v_rgb`, produziria a mesma assinatura. A memória da máquina não tem ECC. **Não se separa o cálculo da leitura com este dado.**

**Ponto a favor de o evento ser real**, sem demonstrar: em D4, `v_rgb` é soma inteira, associativa e comutativa (§11.3). **A ordem das invocações não pode produzir esse evento.** Se ele está no cálculo, algum termo foi diferente, ou faltou, ou se duplicou. Seria uma fonte de natureza diferente da não-associatividade: condição de corrida ou leitura de dado velho.

**Taxa:** 1 evento em 6.812 repetições, somando os dois pontos. O IC 95% exato de Poisson é **[3,7·10⁻⁶ ; 8,2·10⁻⁴]** por repetição. Supor a mesma taxa nos dois pontos não está fixado. Por ponto: 1/3406 no 16.050, e no 29.950 zero eventos, com limite superior de 8,8·10⁻⁴.

### Relação com o par denso de 2026-10-07, compatível e não demonstrada

No par denso, a primeira diferença apareceu no forward do passo 16.165, com `n_contributors` diferente. Um evento só em `v_rgb` altera apenas os SH, e **não** mudaria `n_contributors` no forward seguinte. Portanto este evento, tal como observado, **não explica** aquele par. Uma classe mais ampla, "erro raro e transitório de termo no backward", que pudesse atingir também o gradiente de cônica, explicaria, via escala ou rotação, a hipótese (b) de 2026-10-07. É conjectura.

### Observação lateral, sem interpretação

Esta execução termina com **5.940.699** gaussianas. A série de D4 vai de 5.940.141 a 5.940.245, com amplitude de 104. A execução fica 454 acima do máximo das 10. A da fase 1 terminou no valor modal, 5.940.143. A configuração é a mesma do `tcc_runner.py` (`TrainerConfig()` padrão, mesmos caminhos, `TRAIN_DEVICE` 0), e antes do passo 16.050 não há repetição nenhuma. **Uma observação não é distribuição.** Fica registrado.

### Próximo teste possível, a decidir com o aluno: captura do evento

Para separar cálculo de leitura e caracterizar o termo:
- guardar na RAM o array de referência da primeira repetição;
- quando o hash de um buffer divergir da referência, **reler imediatamente o mesmo buffer da GPU sem recalcular**. Se a releitura der o hash normal, foi a leitura. Se reproduzir o hash divergente, o conteúdo da GPU difere, e foi o cálculo;
- gravar o diff elemento a elemento em `.npz`: índices, valores e XOR de bits. **Um único bit trocado** sugere falha de memória. **Uma diferença do tamanho de um termo plausível** sugere corrida.

O custo extra só existe quando há evento. Com taxa ~1/3406 no passo 16.050, capturar com ~95% de chance exige ~10⁴ repetições, ~4,5 h nesse ponto.

## 2026-10-14 — Captura de eventos: implementada, testada e **fixada antes de rodar**

Decisão do aluno: seguir com a captura esta noite e redigir o adendo §11.12 do D4b amanhã.

### Verificado no código antes de escrever

Cada acesso a uma propriedade de buffer passa por `buffer_to_array`:
- ele chama `copyFromDevice` (`python_bindings.cpp:29-30`, `on_device` verdadeiro por padrão);
- devolve um `py::array_t` novo (`:585-588`), que o pybind11 copia porque não há objeto-base.

**Reler a propriedade, portanto, copia de novo da GPU sem recalcular**, que é a premissa da releitura.

Em D4, os `v_*` são declarados `float` no binding (`:671-674`) e contêm bits de `int32`, porque o D4 mudou só os shaders. O diff grava **bits crus** (`uint32`), e a análise reinterpreta conforme o degrau.

### O que o script faz (`testar_estagios.py`)

- **Referência** = repetição 0 de cada ponto, com hash e cópia do array na RAM (~250 MB nos pontos tardios).
- Quando o hash diverge da referência: **releitura imediata** do mesmo buffer, depois o diff elemento a elemento contra a referência. Grava `evento_<degrau>_p<passo>_rep<i>_<buffer>.npz` com `idx`, `ref`, `obs`, `releitura` e `shape`, e registra no JSON os três hashes, o popcount do XOR e o número de elementos diferentes. Imprime uma linha `EVENTO` na hora.
- No máximo 10 capturas por buffer por ponto. As demais divergências só são contadas.
- **Linha de progresso a cada 100 repetições**, a correção prometida na entrada anterior.

### Regra de leitura, fixada agora

- **releitura == observado:** o conteúdo **na GPU** difere. O cálculo, ou a memória da GPU depois dele, produziu outro valor;
- **releitura == referência:** falha **transitória da leitura** (GPU → staging → RAM → numpy → hash), e não do cálculo;
- **releitura igual a nenhum dos dois:** instável, não classificado;
- **padrão do diff:**
  - um elemento com popcount 1 **sugere** bit trocado, falha de memória;
  - poucos elementos com diferença do tamanho de um termo, em quanta inteiros de D4, **sugerem** termo diferente no cálculo.

  **Sugere, não demonstra.** Um bit trocado na VRAM depois do cálculo também persiste na releitura. Nesse caso "releitura == observado" não separa cálculo de memória da GPU, e só o padrão do diff orienta.

**Execução fixada:** D4, **somente o passo 16.050**, **K = 10.000**. Com a taxa do único evento observado (1/3406), a probabilidade de pelo menos uma captura é de ~95%.
- **Custo, a partir do medido** (1,637 s por repetição no 16.050): ~4 h 33 min de repetições, mais ~20 min de treino e avaliação, **~4 h 55 min**;
- **declarado:** o estado no passo 16.050 é o de uma trajetória nova, e não o da fase 2, porque as execuções de D4 divergem depois de ~13.500. Se a taxa depender do estado, ela pode ser outra;
- **se não houver evento:** limite superior de 95% de 3,0·10⁻⁴ por repetição neste estado. O evento da fase 2 continua sem caracterização.

### Testes no Mac

O stand-in imita o binding nos pontos relevantes:
- cada leitura devolve uma cópia nova;
- os `v_*` são `int32` expostos como `float`;
- os métodos sem guard falham fora de lote.

Eventos injetados:
- termo +37 na gaussiana 123: capturado como "releitura == observado", idx 370, ou seja gaussiana 123 e componente 1, com diferença de **+37** em inteiro;
- bit trocado só numa leitura: "releitura == referência", popcount 1;
- bit trocado no conteúdo: "releitura == observado", popcount 1, diferença de 2²⁰;
- buffer vazio numa repetição: tamanhos [256, 0], sem `.npz`, sem erro;
- repetição 0 anômala: 59 divergências e só 10 capturas, com multiplicidades [59, 1] que mostram a referência anômala;
- sem evento: lista vazia;
- progresso a cada 100 repetições;
- `--progresso -1` rejeitado.

## 2026-10-15 — Captura: **nenhum evento em 10.000 repetições**; caça à fonte residual encerrada; D4b com escala de cônica por faixa de passos

### Resultado da captura

JSON em `pivo-reprodutibilidade-3dgs/dados/estagios/estagios_D4_captura.json`, SHA-256 `f7b075ba…`, ainda não commitado. A tabela final foi colada pelo aluno.

**Integridade:**
- commit de diagnóstico `48324989…` sobre D4, patch `f44cd7c9…`;
- módulo recompilado 0,3 s antes do início;
- `completo: true`, K=10.000, passo 16.050;
- de 2026-10-14T22:58Z a 2026-10-15T03:30Z, ou seja **4 h 32 min**, contra os 4 h 33 min de repetições previstos;
- mediana de 1,536 s por repetição, máximo 1,598 s, nenhuma acima de 1,5× a mediana;
- avaliação PSNR 27,00, SSIM 0,847, LPIPS-Alex 0,100.

**Resultado:** nos 6 buffers, 1 hash em 10.000 repetições, **zero divergências da referência e zero eventos capturados**. Limite superior de 95% da taxa por repetição neste estado: **3,0·10⁻⁴**.

**O evento da fase 2 (`v_rgb`, 1 em 3.406, trajetória A) fica sem caracterização.** Não se sabe se foi cálculo ou leitura.

Somando todas as execuções em D4, é 1 evento em 16.952 repetições de estágio (140 + 3.406 + 3.406 + 10.000), com IC 95% de Poisson ≈ [1,5·10⁻⁶ ; 3,3·10⁻⁴]. **É descritivo:** a soma supõe a mesma taxa em estados diferentes, o que não foi fixado.

### Observação que exige escrutínio, sem interpretação

Número final de gaussianas nas três execuções do teste de estágios em D4:

| execução | repetições antes do passo 15.000 | N final |
|---|---|---|
| fase 1 | sim (1.050, 5.050, 10.050, 14.050) | 5.940.143, o valor modal da série |
| fase 2 | não | **5.940.699** |
| captura | não | **5.940.524** |
| série D4, 10 execuções | — | 5.940.141 a 5.940.245 |

As duas execuções sem repetições antes do fim da densificação ficaram acima do máximo da série. Por permutabilidade, uma execução nova cai fora da faixa de 10 com probabilidade ~2/11. Duas seguidas, as duas acima, têm probabilidade de ~3%. **Pode ser acaso.**

Há também uma **lacuna minha**: o `testar_estagios.py` **não grava `ambiente.json`** (Mesa, libc, boot), ao contrário de `run_degree.sh`. Por isso não posso excluir uma mudança de ambiente entre a série e estas execuções. Todo script de execução daqui em diante grava o ambiente.

### Decisão do aluno: encerrar a caça à fonte residual

Afirmação que vai para o texto, com a força declarada:
- **a acumulação em `float` é a fonte dominante.** Em estado fixo, o backward de D3 deu um gradiente diferente em 140 de 140 repetições, enquanto forward e perda foram idênticos;
- **em D4 resta uma fonte rara, não identificada:** 1 evento em ~1,7·10⁴ repetições de estágio, sem separar cálculo de leitura. Nas trajetórias, a divergência de D4 continua aparecendo só depois do passo ~13.500;
- **por inferência, e não demonstrado:** a fonte residual não é a não-associatividade, porque em D4 a soma é inteira.

### D4b: decisões do aluno, e um erro meu corrigido antes de qualquer texto

- **Escala de cônica por faixa de passos**, opção (b). As outras eram (a) escala fixa pelo regime e (c) escala fixa intermediária.
- **Erro meu, na pergunta ao aluno:** sugeri como exemplo "`s=18` antes do passo 1.000 e `s≈27` depois". **Os dados de `dados/gradientes/` desmentem isso.**
  - O máximo do gradiente acumulado de cônica, maior das 3 repetições, continua alto entre os passos 1.000 e 3.000:
    - `conic_0`: 87,5 / 91,6 / 257;
    - `conic_1`: 38,2 / 130 / 133;
    - `conic_2`: 27 / 48,3 / 70,3.
  - Ele só cai a partir do passo 5.000: no máximo 3,76 (`conic_0`, passo 25.000), 1,39 e 0,866.
  - Com `s=27`, o acumulador comporta até 16 e estouraria no passo 3.000.
  - A regra `floor(log2(2³⁰/máx))` dá `s` = 21, 22 e 23 para a faixa de 500 a 5.000, e 28, 29 e 30 a partir de 5.000.
- **Lacuna dos dados:** as 16 amostras não incluem nenhum dos resets de opacidade dos passos 6.000, 9.000 e 12.000, nem passos logo depois deles. O passo 3.000, que é reset, tem o maior máximo da fase intermediária. **Fixar os cortes com estes dados seria fixá-los no escuro.**
- **Conferido no código:** os máximos dos passos de densificação são válidos para a cônica. O pós-backward lê e escreve `v_xy_vs`, mas não toca `v_inv_cov_vs_opacity` (`gs_trainer.cpp:806-818` em D4). `v_xy_vs` pode ter sido alterado nesses passos, o que não afeta o D4b.
- **Conferido no código, para a implementação:**
  - o produtor recebe `uniforms.step = S` (`utils.slang:761`; `python_bindings.cpp:536`);
  - o otimizador recebe **`S+1`** (`python_bindings.cpp:476`, `gs_trainer.cpp:703`);
  - uma escala por passo tem de usar `step` no produtor e `step − 1` no otimizador, por uma única função compartilhada;
  - **D4b continua sem mudança no C++.**
- **Decisão do aluno: medir antes de fixar o §11.12.** Medição densa do gradiente de cônica em D3, com custo medido antes.
- **Decisão do aluno: manter o plano completo**, com todas as iterações antes de escrever. Meu alerta, registrado uma vez: o congelamento passa de ~20/out, e a escrita começa depois, sobre uma janela menor que 17 dias.

### Medição densa preparada: `experimentos/medir_conica_d4b.py`

**O que mede.** Depois de cada `train_step` amostrado, em D3, o script lê `v_inv_cov_vs_opacity` (N × 4: `conic_0`, `conic_1`, `conic_2`, `opacity`). Por componente, grava:
- `max_abs` e `min_abs` não nulo, **exatos**;
- contagens de zeros, NaN e Inf;
- **histograma de expoente base 2** (`np.frexp`), `hist_exp2[e]` = número de valores com |g| em [2^(e−1), 2^e).

O histograma permite avaliar **qualquer** escala `s` depois: quantos valores viram zero, |g| < 2^−(s+1), e quantos estouram o acumulador, |g| ≥ 2^(31−s), com resolução de fator 2. Mede-se o **acumulado** por gaussiana, como em `dados/gradientes/` e na regra do §11.2. Termos individuais não são medidos, a mesma limitação do §11.9.

Escolhi o histograma em vez de percentis: os percentis exigiriam ordenação parcial de ~6 M valores por componente a cada amostra, e não permitiriam reavaliar escalas depois.

**Amostragem, fixada:** **3.316 amostras por repetição**:
- passos 0 a 99, todos;
- um a cada 10 até o fim;
- todos os passos de R a R+50, para R = 3.000, 6.000, 9.000 e 12.000;
- todos os passos de 15.000 a 15.050;
- o passo 29.999.

O reset de opacidade roda no pós-backward dos passos múltiplos de 3.000 (`gs_trainer.cpp:1027` em D3), e só antes de `refine_stop_iter` = 15.000 por causa do retorno em `:802`. Portanto os resets são 3.000, 6.000, 9.000 e 12.000, e o primeiro gradiente afetado é o de R+1.

**Proteções:**
- exige a tag D3 e a árvore limpa;
- **aborta se o módulo carregado tiver os métodos `*_guarded`**: isso indica que ele foi compilado numa branch `estagios-*` e não em D3. É o detector de binário velho que faltava, porque o `checkout` não troca o `.so`;
- não sobrescreve dados;
- NDJSON gravado e descarregado a cada amostra, e o meta com `completo`;
- **`ambiente.json` no início e no fim**, com os mesmos pacotes de `run_degree.sh:56-65`. Aviso impresso se `boot_id` ou pacotes mudarem durante a execução.

**Modo `--custo`:** treina até o passo 10.500 e amostra 50 passos de 10.010 a 10.500 (N ≈ 5,2 M). Imprime a mediana por amostra e a projeção para o cronograma completo, como cota superior. **O prazo só é estimado depois desta medição.**

**Testes no Mac:**
- redução contra força bruta (`math.frexp`), com 5.012 valores: denormais, negativos, ±0, NaN, Inf e valor perto do máximo de `float32`. **Todas as verificações passam**;
- buffer vazio, só zeros, só NaN e coluna não contígua, esta igual à versão contígua;
- ponta a ponta com fork falso: 3.316 linhas e `completo: true`, buffer vazio no passo 3.001 sem erro, NaN e Inf contados na componente certa, pico injetado de 257 no passo 3.005 caindo no bloco pós-reset [3000, 3051) do resumo;
- abortos: arquivo já existe (1), treino interrompido no passo 5.000 (2, com 635 linhas preservadas e `completo: false`), módulo com o patch de estágios (1), SHA errado (1), árvore suja (1), `--rep -1` rejeitado.

**Dois erros apareceram nos testes:**
- **do script:** o modo de custo amostrava até o passo 10.500, mas treinava com `train_steps` = 10.500, cujo último passo é o 10.499. Daria 49 amostras e o aborto 2. Corrigido para `train_steps` = 10.501;
- **do teste, não do script:** o dado de teste tinha 3,5·10³⁸, acima do máximo de `float32`, o que gerou um Inf a mais. Os outros "erros" eram filtros do próprio teste.

**Custo de disco a declarar:** cada execução grava o `splat.ply` do treino, ~1,4 GB, em `<out>/treino_*`. Não é dado de pesquisa. O mesmo vale para os `treino/` do teste de estágios em `~/tcc-runs/estagios/`.

### Custo medido, e um achado: **a amostragem esparsa subestimou o máximo do regime em ~2 ordens de grandeza**

Execução `--custo` em D3, saída literal colada pelo aluno:
- `custo: 50 amostras, mediana 0.520 s/amostra`;
- projeção para o cronograma completo (3.316 amostras): `<= 29 min de amostragem por repeticao, mais o treino`;
- avaliação do modelo truncado no passo 10.500: PSNR 26,42, SSIM 0,839, LPIPS-Alex 0,106. É compatível com treino incompleto, e não é dado do D4b.

**Estimativa a partir do custo medido:** ~29 min de amostragem, mais ~16 min de treino, mais ~2 min de avaliação e `.ply`, o que dá **~47 min por repetição** e **~2 h 20 min** para as 3 em sequência. A cota é superior, porque as amostras do início têm N menor.

**Achado.** Máximo do gradiente acumulado nos passos 10.010 a 10.500, numa única execução e 50 amostras: **`conic_0` = 35,3, `conic_1` = 51,6, `conic_2` = 20,9**, e opacidade 0,00203. Nas 16 amostras esparsas de `dados/gradientes/`, os passos 10.000 e 12.500 tinham dado 0,09 a 0,87 (o maior das 3 repetições).

- **O "máximo de 3,76 a partir do passo 5.000", registrado mais acima nesta entrada, é artefato da amostragem esparsa.** Uma escala `s≈28`, com capacidade 8, teria estourado com frequência no regime.
- **Isto confirma que a decisão de medir antes de fixar o §11.12 era necessária.** Com os dados antigos, o D4b teria sido desenhado errado pela segunda vez, pelo mesmo mecanismo do erro de D4: uma estatística agregada sem olhar a estrutura temporal.
- **Escrutínio:**
  - é uma execução e 50 amostras;
  - a janela inclui passos de densificação, mas a densificação não toca este buffer, como verificado no código;
  - **o padrão sugere picos raros**, porque o máximo por passo varia em ordens de grandeza entre passos próximos. Se for isso, nem a amostragem a cada 10 passos captura o máximo verdadeiro. A regra do adendo terá de usar a **cauda do histograma** (quantas gaussianas excedem cada capacidade, por passo) e não só o máximo.

**Alternativa de desenho que o achado abre, não decidida:** `clamp` **por termo** em ±L/2ᵏ, em vez de ±L.
- Continua função pura do termo, e preserva a associatividade (D-4).
- Garante que o acumulador **nunca** estoura para gaussianas que tocam até 2ᵏ tiles, porque o per-splat soma um termo por tile.
- O preço é saturar termos grandes.
- Fica para o adendo, decidido com os dados das 3 repetições.

## 2026-10-15 — Medição densa da cônica em D3: **faixa dinâmica de mais de 40 bits; D4 zerou 90–98% do gradiente de cônica e estourou o acumulador**

### Dados e integridade

Em `pivo-reprodutibilidade-3dgs/dados/conica/`, ainda não commitados:
- `conica_rep0{0,1,2}.ndjson.gz`, comprimidos com `gzip -9 -n`;
- os `_meta.json`.

SHA-256 dos NDJSON **descomprimidos**, conferidos depois de descomprimir: rep00 `582ef2c5…`, rep01 `01d1088e…`, rep02 `d50f92d2…`.

**Integridade das 3 repetições:**
- `completo: true`, 3.316 de 3.316 amostras e 30.000 chamadas de `train_step`, no commit D3;
- módulo recompilado às 10:24Z, antes de todas;
- `boot_id` `d6ccf370` constante do início ao fim;
- **pacotes idênticos aos da série D4** (Mesa 25.2.8, libc 2.39-0ubuntu8.9, Python 0.17), com o RADV na RX 9070 XT;
- 0 NaN e 0 Inf;
- logs sem erro;
- duração de 43 a 44 min cada, contra ~47 min estimados pelo custo.

O boot é outro, não o da série D4 (`8d0e782c`); kernel e pacotes coincidem.

### Resultado 1: a faixa dinâmica do gradiente acumulado de cônica passa de 40 bits

- Valores não nulos de |g| no regime, passos 5.000 a 30.000, quantis 10/50/90/99%: **~2⁻³⁵, 2⁻²⁸, 2⁻²² e 2⁻¹⁷**.
- Máximo por passo, com picos: até **7,7·10⁶** entre 1.000 e 2.000, e **2,3·10⁶** entre 20.000 e 30.000, ou seja ~2²³. A mediana dos máximos por passo no regime fica em 0,1–2. Os picos são raros e esparsos.
- **As 16 amostras de `dados/gradientes/` davam máximo de 3,7·10³.** Subestimaram o máximo em ~3 ordens de grandeza.
- Os valores grandes são plausíveis fisicamente, não lixo: ∂α/∂cônica é proporcional a Δx², e gaussianas que cobrem muitos pixels dão Δx² ~ 10⁶ px². É explicação, não verificação.

### Resultado 2: o que isto diz sobre D4, que é **limitação a declarar** e não afeta H3.4

Calculado pelos histogramas, sobre o acumulado por gaussiana. Sendo `s` a escala, um valor vira zero se |g| < 2^−(s+1) e estoura se |g| ≥ 2^(31−s).

| faixa de passos | fração zerada com `s=18` (D4) | passos com ≥1 estouro com `s=18` |
|---|---|---|
| 0–1.000 | 0,58 | 0,08 |
| 1.000–3.050 | 0,90 | 0,11 |
| 3.051–5.000 | 0,95 | ~0 |
| 5.000–15.050 | 0,97 | ~0 |
| 15.050–30.000 | 0,98 | 0,01–0,02 |

Valores de `conic_0`. `conic_1` e `conic_2` são semelhantes, ver os JSON. Daí:
- **D4 zerou de 90 a 98% dos gradientes de cônica não nulos a partir do passo 1.000.** Isso quantifica a hipótese de 2026-10-01, que passa de "provável" a medida, sobre trajetórias de D3;
- **D4 também estourou o acumulador**, em pelo menos uma gaussiana, em ~6–11% dos passos entre 0 e 3.050. O estouro é wraparound (§11.3) e devolve gradiente com valor e sinal arbitrários. A "folga de 2,1× a 2,8×" do §11.2 estava errada, porque saiu de 16 amostras;
- **a opacidade também estourou em D4:** o máximo denso é 0,288, contra capacidade de 0,125 com `s=34` (6,4× o máximo esparso). Isso ocorreu em 18 de 9.948 passos amostrados, a maioria entre 100 e 3.050, incluindo o 3.001, logo depois do reset;
- **`xy` e `rgb` não foram medidos densamente.** Não se sabe se estouraram;
- **nada disto afeta H3.4**, porque a soma modular continua associativa. **Afeta a qualidade de D4, e a afirmação de que D4 é uma intervenção limpa.** É a terceira vez neste projeto que uma estatística sem estrutura temporal produz uma conclusão errada (2026-09-23, 2026-10-01, e esta).

**Leitura, como inferência:** o Adam normaliza cada parâmetro por √v. Um gradiente pequeno, mas não nulo, ainda move o parâmetro; um gradiente zerado sempre não move. Por isso o que importa é a **fração zerada por contagem**, e não por massa. É coerente com o diagnóstico de 2026-10-05, em que só ~24% das gaussianas tinham escala ou rotação diferentes entre execuções de D4. É coerente, não demonstrado.

### Resultado 3: nenhuma escala de 32 bits resolve, e a premissa da opção (b) mudou

- Com escala fixa e sem `clamp` adicional, subir `s` troca zeros por estouros. Com `s=28`, a fração zerada no regime ainda é de 35–40%, e há estouro em 5–29% dos passos. **Faixas de passos não resolvem**, porque os picos aparecem em todas as fases, inclusive entre 20.000 e 30.000.
- **`clamp` por termo em ±L/2¹³ elimina o estouro por construção.**
  - O K máximo medido é 4.346 tiles, menor que 2¹³. O per-splat soma um termo por tile, como conferido no código mais tarde nesta mesma data. *(Correção, no mesmo dia: a primeira redação dizia "exatamente a grade inteira de 82 × 53". **É inferência**, a partir de 4.346 = 82 × 53 e da resolução presumida de `images_4`, que não foi lida. Vira a verificação V0 do §11.12.)*
  - É função pura do termo e preserva a associatividade (D-4).
  - Com ele, `s` passa a regular só a troca entre zerar e saturar.
  - Proxy de saturação: fração de valores **acumulados** ≥ 2^(18−s). Os termos individuais não foram medidos, então o proxy não é uma cota exata.

  | `conic_0` | zerada (0–3.050 / 3.051–15.050 / 15.051–30.000) | saturada, proxy (mesmas faixas) |
  |---|---|---|
  | `s=28` | 0,19 / 0,35 / 0,38 | 1,5·10⁻³ / 3,1·10⁻⁴ / 2,3·10⁻⁴ |
  | `s=30` | 0,12 / 0,21 / 0,24 | 5,3·10⁻³ / 1,0·10⁻³ / 6,7·10⁻⁴ |
  | `s=31` | 0,09 / 0,16 / 0,19 | 9,7·10⁻³ / 1,7·10⁻³ / 1,1·10⁻³ |

- **Por inferência:** sob o Adam, saturar é próximo de um *clipping* de gradiente, que costuma ser benigno, e zerar congela o parâmetro. Isto favorece `s` alto com `clamp`.
- **Consequência para a decisão do aluno:** a opção (b), escala por faixa, foi escolhida para evitar estouro do acumulador. **Com o `clamp` em L/2¹³ o estouro deixa de depender da escala**, e as faixas trazem pouco: só um pouco menos de saturação no início. Elas também acrescentam o acoplamento produtor/otimizador (`step` contra `step − 1`). **A decisão precisa ser revista com o aluno antes do adendo.**
- **Para o texto, é um achado em si:** acumulação determinística em ponto fixo de 32 bits **não representa** a faixa dinâmica do gradiente de cônica do 3DGS. Ela força uma troca de qualidade (zerar, saturar ou estourar), e não é uma substituição neutra do `float`.

### Decisões do aluno sobre o D4b, revistas com os dados densos

As opções foram apresentadas com as tabelas de fração zerada e saturada à vista. Escolhas do aluno:
1. **Escala única + `clamp` por termo em ±L/2¹³**, em vez de faixas de passos. A opção (b), escolhida antes dos dados densos, foi substituída, porque o motivo dela, evitar estouro, deixou de depender da escala;
2. **`clamp` só nos 3 componentes de cônica.** Opacidade, `xy` e `rgb` ficam como em D4, e a comparação D4 × D4b isola a cônica. A alternativa, nos 9 componentes, custaria 13 bits de capacidade a componentes sem medição densa;
3. **Regra para `s`:** o maior `s` com proxy de saturação ≤ 10⁻³ no regime.

**Resultado da regra, por `experimentos/analisar_conica_d4b.py`:** **`s=30` nos três componentes**:
- regime de 3.051 a 30.000: saturação de 6,4 a 8,2·10⁻⁴, contra 1,1 a 1,4·10⁻³ com `s=31`; fração zerada de 0,22 a 0,24;
- o mesmo `s` com o regime de 5.000 a 30.000, e em cada repetição isolada.

Confirmado no código de D4 antes de redigir: **um termo atômico por par (gaussiana, tile)**.
- O laço de lotes de pixels roda uma vez, porque `PIXEL_BATCH_SIZE = TILE_SIZE` (`alphablend_shader_bwd_per_splat.slang:12, 87`).
- Cada gaussiana do tile é tratada uma única vez entre as rodadas (`:89-97`).
- Os atômicos estão em `:199-209`.
- O otimizador desquantiza a cônica por `d4_desq_conic_opacity` (`fused_projection_backward_optimizer.slang:120`), que lê as constantes de `d4_fixed_point.slang`.
- O D4b continua **sem mudança no C++** e **sem acoplamento com o passo**.

**Limite por termo:** `Lc` = 2¹⁸ − 1 = 262.143,0, exato em `float32`. **Não** pode ser L/2¹³. Esse valor, 262.143,984375, também é exato em `float32`, mas o `round` o leva a 262.144, e 2¹³ × 262.144 = 2³¹ estouraria por uma unidade. Conferido numericamente. *(Correção, minutos depois: a primeira redação justificava a escolha por "L/2¹³ não seria exato", o que é falso.)* Com grade ≤ 2¹³ tiles, |acumulado| ≤ 2.147.475.456 < 2³¹ − 1.

### Redigido: `pre-registro.md` §11.12, acrescentado ao fim, RASCUNHO

O adendo contém:
- **motivação e ordem real dos eventos:** os parâmetros foram fixados depois de D4, da medição densa e das tabelas de troca;
- os dados que o fundamentam, com SHA-256;
- **a correção datada de §11.2 e §11.9, sem editá-los:** a folga estava errada e D4 estourou;
- a transformação, com `s=30`, `Lc` e a regra;
- a organização no fork: 2 `.slang` alterados, nenhum C++;
- **as verificações V0–V5.** V0 confere a grade de `images_4` na Ubuntu: a resolução **não foi lida** e o "82 × 53" era inferência minha, já corrigida acima. V2 prevê 2 `.spv` alterados e `default_update_state` bit-idêntico. V5 confere as constantes de escala no `.spv`;
- **os critérios:**
  - H3.4b pela identidade de hash, com expectativa de refutação;
  - §5.2 D3 (N=30) × D4b;
  - **QD4b**: |mediana D4b − mediana D3| < 0,10 dB;
  - **a leitura de cada desfecho**, fixada antes de rodar;
- limitações: entre elas, ~23% ainda zerados e o proxy sobre o acumulado;
- **desvios D-8, D-9 e D-10.**

**Ele só vale quando commitado, e tem de ser commitado antes da série.** Falta a revisão do aluno.

## 2026-10-15 — §11.12 **vinculante** (`5a3b4a7`); V0 aprovada; patch de D4b e verificador prontos

### Vinculação

O §11.12 foi commitado pelo aluno em **`5a3b4a7`**, em 2026-10-15T19:34:22−03:00, e está no remoto. A mensagem do commit é "apresentacao v2", porque ele junta o adendo, os dados de `dados/conica/`, o `analisar_conica_d4b.py`, o caderno e arquivos da apresentação. O conteúdo do adendo é verificável por `git show 5a3b4a7 -- pivo-reprodutibilidade-3dgs/pre-registro.md`. Nenhuma execução de D4b aconteceu antes desse commit.

### V0

Saída literal na Ubuntu: a primeira imagem, em ordem alfabética, de `garden/images_4` tem `(1297, 840)`. Daí ⌈1297/16⌉ × ⌈840/16⌉ = 82 × 53 = **4.346 tiles ≤ 8.192**. A inferência anterior se confirma. **Ressalva:** só uma imagem foi lida. A conferência de todas fica para a entrada do SHA.

### Patch: `experimentos/d4b/d4b.patch`

Gerado a partir das fontes de D4, numa cópia extraída por `git archive`. A árvore do clone no Mac, que tem o rascunho de D4 sem commit, não foi tocada.

- **`d4_fixed_point.slang`:**
  - `D4_ESC_CONIC_{0,1,2}` passam a 1073741824,0 (2³⁰);
  - `D4_INV_CONIC_{0,1,2}` passam a 9,313225746154785e−10 (2⁻³⁰);
  - novos `D4B_LIM_CONICA` = 262143,0 e `d4b_quantizar_conica`;
  - comentário com a garantia e com o motivo para não usar L/2¹³;
  - `xy`, opacidade, `rgb`, `D4_LIM` e `d4_quantizar` **intocados**.
- **`alphablend_shader_bwd_per_splat.slang`:** novo macro `_ATOMIC_ADD_CONICA`, usado **só** nos 3 sítios de cônica. Os outros 6 seguem com `_ATOMIC_ADD_FIXED`.

**Conferido:**
- os três literais leem **exatamente** como 2³⁰, 2⁻³⁰ e 262.143 em `float32`;
- o patch aplica limpo sobre D4;
- a árvore resultante difere de D4 **só** nos 2 `.slang`;
- 1 definição de macro e 3 usos.

### Extrator de constantes, para V5: `constantes_float32` em `inspecionar_spirv.py`

Função acrescentada, sem mudar o comportamento existente. **Validada nos `.spv` versionados**, onde sei o que tem de aparecer:
- `rasterize_backward_1`: D3 tem 6 constantes e nenhuma das escalas; D4 tem 14, entre elas 2¹⁸, 2²⁰, ±L, 2³⁴, 2⁴⁴, 2³⁷ e 2³⁸;
- `fused_projection_backward_optimizer`: D3 sem escalas; D4 com 2⁻¹⁸, 2⁻²⁰, 2⁻³⁴ e 2⁻⁴⁴;
- `default_update_state`: só 2⁻⁴⁴ em D4.

**Nenhuma dessas constantes existe em D3**, então o critério da V5 é inequívoco.

### Verificador: `experimentos/compilar_d4b.py`

Derivado de `compilar_d4.py`, com a mesma função de perfil e o mesmo comando de compilação. O que ele faz:
- recusa rodar se a árvore não for "D4 + os 2 `.slang`";
- compila os 16 jobs dos 3 grupos;
- V2: alterados contra D4 = exatamente os 2 `.slang` e os 2 `.spv`, com `default_update_state` **bit-idêntico**;
- V3: `OpAtomicIAdd` ×9, `OpAtomicFAddEXT` ×0, sem a extensão, e `Round`, `FClamp` e `OpConvertFToS` com a **mesma** contagem de D4;
- V4: otimizador com atômicos e `OpConvertSToF` iguais aos de D4;
- V5: as constantes, como no §11.12.5;
- grava as constantes de D4 e de D4b no relatório.

**Testes no Mac:** o fork falso é o D4 extraído, com tag `D4`, e o `compile_shaders.py` real gerou os 16 jobs. O `slangc` falso devolve os `.spv` reais de D4, alterando só as `OpConstant` conforme o modo.
- Caminho feliz: V2–V5 OK, "PRONTO PARA COMMIT DE D4b", saída 0.
- **Recusas corretas:**
  - compilador que não muda nada: V2 e V5 falham;
  - troca parcial: V5 acusa o 2²⁰ que sobrou;
  - `default_update_state` alterado: V2;
  - aviso do compilador;
  - falha de compilação;
  - sem o patch, com arquivo a mais na árvore, ou com `LD_LIBRARY_PATH` definido: aborto 1.

**O que os testes não cobrem:** o `slangc` real. Só a Ubuntu diz se o compilador emite as constantes como previsto, se o `default_update_state` sai idêntico e se a contagem de `FClamp` se mantém.

## 2026-10-15 — D4b commitado no fork (`8942107f`) e **conferido de forma independente**

O aluno relatou que o `compilar_d4b.py` deu "pronto para commit", e que commitou e deu push no fork. **A saída literal do verificador, o `verificacao_d4b.json` e a V0 completa (todas as imagens) ainda não chegaram**, e ficam pendentes para a entrada datada do pré-registro.

**Conferência independente, feita no Mac a partir do remoto** (`git fetch origin tag D4b` no clone de leitura, que escreve só refs; a árvore com o rascunho de D4 não foi tocada):
- **V1:** `D4b` = `8942107f13e70e2cad6bcf9fe29630568a6565d7`, commit de 2026-10-15T19:43:37−03:00, mensagem "D4b: conica com escala 2^30 e limite por termo 2^18-1 (pre-registro §11.12)". Pai = `22560858…` (D4). `tcc-base` e a tag `D4b` no remoto apontam para ele;
- **fontes:** os 2 `.slang` de `D4b` são **idênticos**, por `diff -rq`, a D4 com `experimentos/d4b/d4b.patch` aplicado;
- **V2:** `git diff --name-status D4 D4b` dá exatamente 4 arquivos: os 2 `.slang`, `rasterize_backward_1.spv` e `fused_projection_backward_optimizer.spv`. **`default_update_state.spv` é bit-idêntico a D4**, como previsto;
- **V3:** o produtor tem `OpAtomicIAdd` ×9, nenhum atômico de `float`, `Round` 9, `FClamp` 9, `FMin` 2 e `OpConvertFToS` 10, **iguais a D4**;
- **V4:** o otimizador tem atômicos e `OpConvertSToF` (17) iguais a D4;
- **V5:**
  - no produtor **saem** 262.144 (2¹⁸) e 1.048.576 (2²⁰), e **entram** ±262.143 e 1.073.741.824 (2³⁰);
  - no otimizador saem 2⁻¹⁸ e 2⁻²⁰, e entra 2⁻³⁰;
  - **nenhuma outra constante muda**;
- SHA-256 dos `.spv` commitados:
  - `rasterize_backward_1`: `9f1977b9d78a5b5657cf7aeeecc8fbc31f4fc5a8839f5be1756285a09d773880`;
  - `fused_projection_backward_optimizer`: `498ec66973902ed78128128fc74baba8c01e61230d6553413dfc0218f1ad651c`.

**Falta para a entrada datada do pré-registro:**
- a V0 completa;
- o `verificacao_d4b.json`, para conferir que os SHA-256 que o verificador aprovou na árvore são os mesmos dos `.spv` commitados, e que não houve aviso do compilador.

**Atualização no mesmo dia:**
- **V0 completa**, saída literal: `185 imagens, tamanhos: {(1297, 840)}`. São 4.346 tiles em todas as imagens;
- **`pre-registro.md` §11.13 redigido**, com o SHA de D4b, V0–V5 pela conferência independente e a ordem dos eventos (§11.12 commitado 9 min 15 s antes de D4b);
- o relatório do verificador continua sem ser visto. O §11.13 o declara como **condição para a série**: os SHA-256 têm de coincidir e não pode haver aviso do compilador. O §11.13 ainda não foi commitado.

**Atualização de 2026-10-16, conferida no remoto antes de olhar qualquer resultado da série:**
- §11.13 commitado em `5957879` (2026-10-15T19:49:40−03:00);
- `dados/toolchain/verificacao_d4b.json` commitado em `2271072` (19:50:40);
- **condição do §11.13 satisfeita**, conferida por mim no arquivo commitado:
  - relatório gerado às 22:42:45Z, ou 19:42:45−03:00, antes do commit de D4b;
  - `slangc 2026.2.1`, base D4;
  - `sha256_D4b` dos 2 `.spv` **iguais** aos commitados;
  - 16 jobs, 0 falhas, 0 avisos;
  - V2–V5 `True`, `default_update_state` bit-idêntico.
- O aluno informou que a série `run_degree.sh D4b 0 9` terminou. Os horários reais de início ficam para conferir no `ambiente-serie-*.json` e nos logs coletados.

## 2026-10-16 — Série D4b, N=10: **H3.4b refutada; §5.2 sustentado; QD4b satisfeito**. A qualidade volta ao nível de D3 e a dispersão continua reduzida

Dados em `dados/D4b/`, commit `9bc1086`. Análise em `experimentos/analisar_d4b.py`, ainda não commitado. Ele usa o procedimento do §5.2 **idêntico** ao de D3 → D4 (`apresentacao/gerar_apresentacao.py:127-136, 179-189`).

### Integridade, conferida antes de abrir qualquer métrica

- 10 execuções, todas com `vksplat_commit` = `8942107f13…` (D4b), `vksplat_dirty` vazio, que é a saída de `git status --porcelain` (`tcc_runner.py:27`), ou seja árvore limpa, e `train_device 0`;
- boot `d6ccf370`, kernel `-31`, **pacotes idênticos aos da série D4**;
- snapshot da série às 2026-10-15T19:50:43−03:00, ou seja **63 s depois do commit do §11.13** e 3 s depois do commit do relatório. As execuções terminam a cada ~16 min, de 20:07 a 22:30;
- nos 10 logs: RX 9070 XT (RADV GFX1201) marcada como `VIABLE`, `llvmpipe` `NOT VIABLE`, nenhum `USE_EMULATED`;
- **escalonador desligado:** só aparece o timer `RasterizeBackward - 30000`, do caminho sem escalonamento, sem nenhum `_RasterizeBackwardScheduling_*`. É o mesmo padrão de D4;
- `build.log` termina com `Successfully installed vksplat-0.1.0`;
- **sanidade da análise:** o script recalcula D3 → D4 e obtém p = 2,19·10⁻³, razão 0,115 e IC [0,028 ; 0,606], idênticos aos de 2026-10-05.

### Critérios do §11.12.6

| critério | resultado | veredito |
|---|---|---|
| **H3.4b**, identidade de hash | **10 hashes distintos em 10** | **refutada**, como esperado |
| **§5.2 D3 (N=30) × D4b, PSNR**, o pré-registrado | Fligner p = **6,1·10⁻⁴**; razão de IQR **0,120**; IC 95% **[0,038 ; 0,311]** | **sustentado** |
| §5.2, `num_splats` (secundário) | p = 6,8·10⁻⁵. O IQR de D4b é **zero**, porque as 10 execuções têm o mesmo N, e o IC fica degenerado em [0 ; 0] | sustentado, com IC degenerado |
| **QD4b** | \|27,3544 − 27,3882\| = **0,034 dB** < 0,10 | **satisfeito** |

**Leitura, pela primeira linha da tabela de desfechos do §11.12.6, fixada antes de rodar:** a redução de dispersão coexiste com qualidade recuperada. **A atribuição da redução à acumulação inteira se fortalece, e o confundidor de D4 enfraquece.** Ele não some, porque D4b ainda zera ~23% da cônica no regime, pelo proxy medido em trajetórias de D3.

**Sobre a hipótese da perda de qualidade de D4** (2026-10-01): D4b − D4 = **+0,357 dB**, o que recupera ~91% dos 0,39 dB. Pela terceira linha da tabela, a hipótese de que a perda de D4 vinha da quantização da cônica **não é refutada**, e tem agora evidência direta a favor.

### Descritivos

| | mediana | IQR | mín. | máx. | amplitude |
|---|---|---|---|---|---|
| PSNR D3 (N=30) | 27,3882 | 0,0334 | 27,3400 | 27,4344 | 0,0944 |
| PSNR D4 | 26,9977 | 0,0038 | 26,9922 | 27,0165 | 0,0243 |
| **PSNR D4b** | **27,3544** | **0,0040** | 27,3492 | 27,3581 | **0,0090** |
| SSIM D3 / D4 / D4b | 0,8637 / 0,8471 / **0,8638** | | | | |
| LPIPS-Alex D3 / D4 / D4b | 0,0761 / 0,0998 / **0,0759** | | | | |
| `num_splats` D3 / D4 / D4b | 5,81 M / 5,94 M / **5.830.035 nas 10** | 15.694 / 18 / **0** | | | |
| tempo (s) D3 / D4 / D4b | 942,5 / 870,5 / **873,7** | 4,2 / 3,1 / 1,4 | | | |

- **Densificação, grandeza secundária do §4:** em D4b, **as 10 execuções são idênticas nos 144 eventos**, e há uma única sequência completa. Em D4 eram 6 sequências, com divergência a partir do evento 129; em D3, já no evento 0. Os 10 `splat.ply` têm o mesmo tamanho. **A divergência de D4b é só de valor**, sem cruzar nenhum limiar de densificação.
- **Tempo:** D4b é 7,3% mais rápido que D3 e 0,4% mais lento que D4. Fica registrado sem interpretação, como em D4.
- Os 10 PSNR de D4b ficam **dentro** da faixa de D3, e nenhum par em D3, D4 ou D4b difere em ≥ 0,10 dB.

### Escrutínio, porque o resultado é favorável

1. **"Dose-resposta" sem dose controlada.** De D4 para D4b, a supressão da cônica cai de ~97% para ~23% (proxy em D3), e a redução de dispersão fica no mesmo nível (0,115 contra 0,120, com ICs sobrepostos). Isso é o que se esperaria se a redução viesse da acumulação, e não da supressão. **Mas são dois pontos, e os ~23% restantes não foram eliminados.** Uma variante com resolução equivalente à do `float` (64 bits) não está disponível (§10.4) e não foi testada.
2. **O D3 é heterogêneo**, com três estratos de ambiente. Na sensibilidade, que não é critério e não substitui o pré-registrado, D3 `run020`–`029` × D4b dá p = 9,0·10⁻⁴, razão 0,084 e IC [0,029 ; 0,345]. A conclusão não muda.
3. **Opacidade, `xy` e `rgb` herdam os limites de D4**, inclusive os estouros raros de opacidade medidos em D3. D4 e D4b os compartilham, então a comparação entre os dois isola a cônica. A comparação com D3 não isola.
4. **O IC de `num_splats` é degenerado**, porque o IQR de D4b é zero. Reportar como "N idêntico nas 10", e não como um IC.
5. **N=10.** O mesmo N com que D3 → D4 passou.

## 2026-10-16 — Diagnóstico pareado de `.ply` (D3, D4, D4b): desenho fixado e script testado, **antes de qualquer dado**

### Por que o diagnóstico de D3 não pode ser o de D4

O `diagnosticar_ply_d4.py` só compara gaussiana por gaussiana quando as duas execuções têm o mesmo N (`diagnosticar_ply_d4.py:129-130`). Em D3, as 30 execuções têm 30 valores de N distintos, e as densificações divergem no evento 0. **Não existe "a mesma gaussiana" em duas execuções de D3.** O script também abortaria, porque o `origem.txt` aponta para o SSD, de onde os `.ply` de D3 saíram para o HD.

### Desenho, escolhido pelo aluno como o mais completo

**É exploratório:** definido depois de ver os dados, operacionaliza a grandeza secundária do §4 e não substitui nenhum critério pré-registrado.

1. **Um único instrumento para os três degraus:** vizinho mais próximo **mútuo** na posição (scipy `cKDTree`). Mede:
   - a fração pareada;
   - a distância dos pares;
   - nos pares, as diferenças de opacidade (sigmoide), escala (log), rotação (ângulo, com q ≡ −q) e SH (`f_dc`, `f_rest`).
2. **Validação onde a correspondência é conhecida**, em D4 e D4b, pelo índice:
   - *acerto* = fração dos pares mútuos com j = i;
   - *cobertura* = fração dos i cujo par é i.

   Se o pareamento falhar já em D4b, o número de D3 é reportado como sem interpretação.
3. **Escala local:** a distância de cada gaussiana da referência à vizinha mais próxima no próprio modelo, para comparar com a distância entre execuções.
4. **Medida estrita por índice em ULP** onde o N é igual, com a mesma função `comparar` de 2026-10-05. Em D4 ela tem de reproduzir o `diagnostico_ply.json`, o que serve de sanidade.

**Escolhas fixadas agora, antes de calcular:**
- referência contra 9 outras;
- **D3: só `run020`–`run029`** (referência `run020`). É o mesmo estrato de ambiente de D4 e D4b: kernel −31, libc 8.9 e Mesa 25.2.8, conferido nos `ambiente.json`. Assim a diferença entre degraus não fica confundida com ambiente;
- D4 e D4b: referência `run000` contra `run001`–`run009`.

### Script: `experimentos/diagnosticar_ply_pareado.py`

- Cada `.ply` é lido **inteiro para a RAM numa passada sequencial**, com o SHA-256 calculado no caminho e conferido contra o `manifest.tsv`; divergência aborta. O motivo: no HD USB, leitura aleatória por `memmap` seria lenta.
- As diferenças são calculadas em blocos, direto dos `float32` brutos, e os quantis saem de um histograma de log₁₀ com bins de 0,01 década. O máximo e a fração de zeros são exatos. A primeira versão convertia o modelo inteiro para `float64`, ~2,7 GB por modelo, e foi corrigida antes de qualquer teste.
- `--remap` reescreve o prefixo do `origem.txt` para o HD. `--max-pares` serve para medir custo. O JSON é regravado a cada par.

### Testes no Mac

Com `.ply` sintéticos no formato do `writePLY` e casos de resposta conhecida:
- **acumulador de quantis contra `np.quantile`:** erro relativo ≤ 1,2%, abaixo da cota teórica de 2,4%; máximo e zeros exatos; vazio, só zeros, um valor e NaN/Inf tratados;
- **ponta a ponta:**
  - modelo idêntico: pareada 1, acerto 1, byte a byte idêntico, diferenças zero;
  - jitter de 10⁻⁶: acerto 1;
  - permutado: pareada 1, acerto ≈ 0, e "mesmo multiconjunto" pelo teste estrito;
  - **jitter de 0,05, maior que o espaçamento local de 0,02: pareada 0,49 e acerto 0,03.** O instrumento detecta a própria falha;
  - N diferente: pareada 0,9, sem validação;
  - quatérnio negado: ângulo 0;
  - vazio, referência vazia e referência com N=1: sem erro;
  - SHA errado e arquivo ausente: aborto 1; `--max-pares 1` respeitado;
- **dois erros meus, pegos pelo teste com resposta conhecida:**
  - (a) a fórmula estável do ângulo (`atan2`) dava **metade** da rotação, porque o ângulo entre os quatérnios como vetores é φ e a rotação é 2φ. Corrigido para 4·atan2, e conferido com rotações conhecidas de 10⁻³, 0,5, 3 e 3,5 rad, com erro ≤ 1,1% e 3,5 rad voltando a 2π − 3,5. A troca de `arccos` por `atan2` foi feita para tirar um piso numérico de ~4·10⁻⁸ rad, que esconderia diferenças pequenas em D4b;
  - (b) um quantil podia passar do máximo exato, pelo centro do bin, e agora é limitado a ele.

**O que os testes não cobrem:** os `.ply` reais (5,8 M gaussianas, densidade real da cena), o HD USB e a memória da Ubuntu. **O custo será medido com `--max-pares 1` antes das comparações completas.**

### Custo medido e 27 pares executados

**Custo, com 1 par de cada:**
- D4b: 47 s por par, quase tudo na medida estrita por índice; leitura de 2 s pelo SSD;
- D3: 26 s por par, 16 s deles lendo o HD.

**Execução completa:** `D3.json`, `D4.json` e `D4b.json`, todos com `completo: true` e 9 pares; o de D3 com `--remap` para o HD. SHA-256 dos arquivos:
- `D3.json`: `2ccfae9d8c8cf860…`;
- `D4.json`: `82217faf9b19209a…`;
- `D4b.json`: `187f0e9235679cdc…`.

Versionados em `dados/diag_pareado/` (ainda não commitados).

**Sanidade:** nos 4 pares de D4 com N igual (`run002`, `005`, `008` e `009`), a medida estrita por índice é **idêntica em 10 de 10 campos** ao `dados/D4/diagnostico_ply.json` de 2026-10-05. Os outros 5 pares têm N diferente, e neles só o pareamento se aplica.

**Resultados, mediana [mínimo – máximo] entre os 9 pares:**

| | D3 (`run020` × `021`–`029`) | D4 (`run000` × `001`–`009`) | D4b (`run000` × `001`–`009`) |
|---|---|---|---|
| espaçamento local mediano | 1,45·10⁻³ | 1,24·10⁻³ | 1,45·10⁻³ |
| fração pareada | 0,332 [0,332 – 0,332] | 0,744 [0,744 – 0,865] | 0,926 [0,926 – 0,926] |
| distância mediana dos pares | 1,10·10⁻³ | 3,98·10⁻⁴ [2,00 – 3,99·10⁻⁴] | 6,94·10⁻⁵ |
| razão distância / espaçamento | **0,76** | 0,32 [0,16 – 0,32] | **0,048** |
| validação: acerto / cobertura | — (sem correspondência conhecida) | 0,91 / 0,75 (4 pares) | **0,968 / 0,896** (9 pares) |
| rotação nos pares, mediana | 1,46 rad (~84°) | **0** (64% exatamente zero) | 0,028 rad |
| log-escala nos pares, mediana | 1,40 | **0** (66% exatamente zero) | 0,039 |
| opacidade (sigmoide) nos pares, mediana | 0,111 | 0,0094 | 0,0030 |
| `f_dc` nos pares, mediana | 0,248 | 0,065 | 0,012 |
| **estrita**: gaussianas diferentes | — | 0,998 (4 pares) | 0,9991 (9 pares) |
| **estrita**: mediana de log₂ ULP | — | 20 | **18** |
| **estrita**: fração de valores diferentes, posição / opacidade / escala / rotação / SH | — | 0,997 / 0,998 / **0,235** / **0,243** / 0,959 | 0,997 / 0,998 / **0,990** / **0,991** / 0,961 |

**Leituras, com a força declarada:**
1. **D3: sem correspondência recuperável.** Só 33% das gaussianas têm vizinho mútuo, a distância dos pares é ~0,76 do espaçamento local, e as diferenças nos pares (rotação de ~84°, escala ~4×) são de **gaussianas não relacionadas**. D3 está fora do regime em que o instrumento foi validado. **As diferenças nos pares de D3 não são deriva.** O que se afirma é descritivo: dois modelos de D3 diferem na escala do próprio espaçamento entre gaussianas.
2. **D4b: correspondência por índice; deriva de valor de ~2¹⁸ ULP**, ~4× menor que a de D4 (2²⁰). Escala e rotação derivam em ~99% dos valores.
3. **D4: escala e rotação idênticas, bit a bit, em ~76% dos valores entre execuções**, e iguais a zero na diferença dos pares em 64–66% deles. **Isto corrobora diretamente a hipótese de 2026-10-01:** com o gradiente de cônica zerado (90–98%, medição densa de 2026-10-15), escala e rotação dessas gaussianas não eram atualizadas e ficavam iguais entre execuções. Em D4b, com a cônica ativa, o fenômeno desaparece. É uma corroboração por um caminho independente, os `.ply` em vez dos gradientes. Não é demonstração do mecanismo célula a célula.
4. **O instrumento é imperfeito mesmo no regime fácil:** em D4b, com razão 0,048, a cobertura é 0,896. Nos dados sintéticos uniformes ela seria ~1 nessa razão. A geometria real é mais difícil, provavelmente por aglomerados de gaussianas quase coincidentes, o que é inferência.

### Escrutínio pendente, com as leituras fixadas antes de rodar

**(a) A referência é atípica?** Os 9 pares de D4b são quase idênticos entre si: fração diferente entre 0,99911 e 0,99912, distância de 6,90 a 6,96·10⁻⁵. Isso é o esperado se as execuções forem permutáveis, porque cada estatística é média de milhões de valores, **e** também seria o resultado se a `run000` fosse atípica e as outras nove próximas entre si. O PSNR da `run000` (27,3553) fica no meio da faixa, mas isso é indício fraco.
- **Teste:** pares sem a referência, D4b `run001` × `run002` e D3 `run021` × `run022`.
- **Leitura fixada:** razão entre a distância mediana desse par e a mediana dos pares com a referência
  - em [0,8 ; 1,25]: referência **não atípica**;
  - < 0,5: **atípica**, e o desenho de referência única fica enviesado para aquele degrau;
  - entre os dois: inconclusivo.

**(b) Calibração na geometria real.** A referência é deslocada artificialmente, com deslocamento isotrópico gaussiano, mediana igual ao alvo e semente `20261016`, e pareada consigo mesma, com correspondência conhecida.
- **Alvos fixados:** 1·10⁻⁵, 6,9·10⁻⁵ (D4b observado), 2,0·10⁻⁴, 2,5·10⁻⁴, 4,0·10⁻⁴ (D4 observado), 1,1·10⁻³ (D3 observado) e 3·10⁻³. Aplicados à geometria de D4b (`run000`) e à de D3 (`run020`).
- **Leitura fixada:**
  - se a cobertura calibrada nos alvos de D4b e D4 ficar a até ±0,05 das coberturas **observadas** (0,896; 0,75–0,81), a calibração é considerada crível, e a cobertura calibrada no alvo de D3 é reportada como **cota superior** da fração de correspondência correta em D3. É superior porque, em D3, os conjuntos de gaussianas diferem também em estrutura, e não só em posição;
  - se a calibração superestimar os pontos observados por mais de 0,05, ela é reportada como **otimista**, e D3 continua sem número, só com o argumento.

**Implementado:** `--ref`, `--outros`, `--calibrar` e `--so-calibrar`. Testado no Mac:
- constante de Maxwell (1,53817) conferida contra o valor exato e o empírico;
- deslocamento real igual ao alvo;
- cobertura decrescente com a razão;
- `--ref`/`--outros` com par idêntico dá acerto 1;
- entradas inválidas recusadas.

### Resultado das duas verificações, pelas leituras fixadas acima

JSONs em `dados/diag_pareado/` (`D4b_semref`, `D3_semref`, `D4b_calib`, `D3_calib`), ainda não commitados. Todos com `completo: true`.

**(a) A referência não é atípica**, nos dois degraus:
- D4b `run001` × `run002`: distância mediana 6,918·10⁻⁵, contra a mediana de 6,942·10⁻⁵ dos pares com a referência, ou seja **razão 0,997**. Pareada 0,926, acerto 0,968, cobertura 0,896 e fração de gaussianas diferentes 0,99908, iguais às dos pares com a referência;
- D3 `run021` × `run022`: 1,103·10⁻³ contra 1,103·10⁻³, **razão 1,000**, pareada 0,332.

As execuções de cada degrau são permutáveis. A quase igualdade entre os 9 pares é o efeito de médias sobre milhões de gaussianas, e **não** um viés de referência.

**(b) Calibração na geometria real: otimista.** Pela regra, D3 **fica sem número**.

| alvo (deslocamento mediano) | razão / espaçamento | cobertura calibrada, D4b / D3 | observado |
|---|---|---|---|
| 1·10⁻⁵ | 0,007 | 0,999 / 0,999 | — |
| 6,9·10⁻⁵ | 0,048 | **0,973** / 0,971 | **0,896** (D4b) |
| 2,0·10⁻⁴ | 0,138 | **0,904** / 0,902 | **0,809** (D4 `run005`) |
| 2,5·10⁻⁴ | 0,173 | **0,878** / 0,877 | **0,750–0,757** (D4 `run002`, `008`, `009`) |
| 4,0·10⁻⁴ | 0,276 | 0,809 / 0,808 | — |
| 1,1·10⁻³ | 0,76 | 0,561 / 0,562 | — (alvo de D3) |
| 3·10⁻³ | 2,07 | 0,249 / 0,249 | — |

- **A calibração superestima a cobertura observada em +0,077, +0,095 e +0,12** nos três pontos conferíveis, todos acima de ±0,05. Pela leitura fixada, ela é **otimista** e não fornece cota para D3. **D3 fica com o argumento, sem número:** não há correspondência recuperável.
- **Causa provável, inferida e não verificada:** a deriva real tem cauda muito mais pesada que o deslocamento isotrópico gaussiano. Em D4b, o p99 da distância dos pares é 8,3·10⁻⁴. Uma distribuição de Maxwell com a mesma mediana teria p99 ≈ 1,5·10⁻⁴. O pareamento falha justamente nas gaussianas que mais se deslocaram.
- **Refinamento possível e não feito:** reamostrar os deslocamentos reais de D4b, conhecidos pelo índice. Seria mais uma escolha depois de ver os dados, e a regra mandava parar.
- **Achado lateral:** as curvas nas geometrias de D3 e de D4b são **praticamente idênticas** (diferença ≤ 0,002 em cobertura). A densidade da cena é a mesma nos dois degraus, e a dificuldade do pareamento está no deslocamento, não na geometria.

### Diagnóstico de `.ply`: fechado

Para o texto:
1. **D3:** os modelos de execuções nominalmente idênticas **diferem em estrutura**. Os N são distintos e a densificação diverge no evento 0. Pelo pareamento mútuo, só 33% das gaussianas têm par, a distância é ~0,76 do espaçamento local, e os pares diferem como gaussianas não relacionadas. **Não há "a mesma gaussiana" para comparar**;
2. **D4 e D4b:** as gaussianas se correspondem pelo índice, e a diferença é **de valor**. A mediana é de ~2²⁰ ULP em D4 e ~2¹⁸ em D4b, em ~99,9% das gaussianas;
3. **D4:** escala e rotação ficam bit a bit iguais entre execuções em ~76% dos valores, contra ~1% em D4b. É corroboração, pelos `.ply`, de que a cônica zerada congelava a forma dessas gaussianas;
4. **o instrumento de pareamento:** validado onde há correspondência conhecida, com cobertura de 0,90 em D4b e 0,75–0,81 em D4. A calibração por deslocamento isotrópico se mostrou otimista.

## Estado em 2026-10-07 — ponto de entrada para sessão nova

### Atualização de 2026-10-07: ler isto primeiro

O restante desta seção foi escrito em 2026-09-25 e está **superado nos pontos abaixo**. Em divergência, este bloco e as entradas datadas de 2026-10-01 a 2026-10-07 prevalecem.

**D4 feito.** SHA `22560858b0f2…`, adendo vinculante (`pre-registro.md` §11.1–§11.11). Série com N=10, dados em `dados/D4/`.
- **H3.4 refutada** pelo critério do §6: 10 hashes distintos em 10.
- **Pelo §5.2, D3→D4 é a primeira transição sustentada** da escada: PSNR com Fligner p = 0,0022, razão de IQR 0,115, IC [0,028–0,606]. **Há um confundidor aberto:** a escala da cônica zera quase todo o gradiente de covariância.
- **Qualidade −0,39 dB** contra D3. Hipótese não testada: o mesmo artefato da escala da cônica. Erro meu de desenho, porque dimensionei pelo máximo do transiente, e não pelo regime.
- Densificações das 10 execuções idênticas até o evento 129, o passo 13.500. Os `.ply` diferem por **deriva de valor** em ~99% das gaussianas, e não por permutação.

**Onde nasce a divergência de D4:**
- par com 481 amostras: estado **bit-idêntico em todos os 21 buffers até o passo 14.050**;
- par com amostragem densa (todo passo, 5 buffers): idêntico até 16.164, primeira diferença no **forward do passo 16.165**. **A densificação está descartada para este par**, porque termina em 14.900.
- **Origem não determinada:** (a) forward não-determinístico, ou (b) escala ou rotação, que não eram monitoradas, divergindo antes.
- Inventário de código: no caminho ativo de D4 só restam atômicos inteiros de contagem. A fonte residual provavelmente não é atômica. É inferência.

**Teste de estágios, fase 1, feito em 2026-10-14.** Ver a entrada de mesmo título:
- **D3:** forward e perda determinísticos; **backward com um hash distinto em cada uma das 140 repetições**;
- **D4:** nenhuma variação em 140 repetições;
- controle positivo aprovado.

**Fase 2 (2026-10-14) e captura (2026-10-15) feitas:**
- fase 2: 1 evento em `v_rgb` em 3.406 repetições no passo 16.050, e zero no 29.950;
- captura: zero eventos em 10.000 no passo 16.050, numa trajetória nova;
- o evento fica sem caracterização;
- **caça à fonte residual encerrada** por decisão do aluno. A afirmação para o texto está na entrada de 2026-10-15.

**D4b feito (2026-10-16).**
- Commit `8942107f` no fork; §11.12 (`5a3b4a7`) e §11.13 (`5957879`) commitados antes da série; dados em `dados/D4b/` (`9bc1086`).
- **H3.4b refutada**: 10 hashes distintos em 10.
- **§5.2 D3 → D4b sustentado**: p = 6,1·10⁻⁴, razão 0,120, IC [0,038 ; 0,311].
- **QD4b satisfeito**: 0,034 dB abaixo de D3, com SSIM e LPIPS iguais aos de D3. D4b recupera ~91% da perda de D4.
- Densificação idêntica nos 144 eventos e mesmo N nas 10 execuções.
- Leitura pela tabela do §11.12.6: a atribuição da redução de dispersão à acumulação inteira se fortalece; o confundidor enfraquece e não some, porque ~23% da cônica continuam zerados.

Ver a entrada de 2026-10-16. As de 2026-10-15 registram que **D4 zerou de 90 a 98% da cônica e estourou o acumulador**.

**Plano restante, decidido pelo aluno e reconfirmado em 2026-10-15: todas as iterações antes de escrever.** Itens, em ordem:
1. ~~teste de estágios~~ **feito**;
2. ~~D4b~~ **feito** em 2026-10-16;
3. ~~diagnóstico de `.ply` em D3~~ **feito** em 2026-10-16, como diagnóstico pareado de D3, D4 e D4b, com validação e calibração. Ver a entrada de mesmo título;
4. H4, comparação com os valores publicados do VkSplat;
5. H3b, executar ou declarar não executada;
6. cópia em nuvem dos `.ply`.

<!-- plano anterior, de 2026-10-05, mantido como registro:
1. teste de estágios;
2. diagnóstico de `.ply` em D3, com os arquivos no HD externo;
3. **D4b**, com escala da cônica dimensionada pelo regime, que exige o adendo §11.12 **antes** de rodar;
4. H4, comparação com os valores publicados do VkSplat;
5. H3b, executar ou declarar não executada;
6. cópia em nuvem dos `.ply`.
-->

**Infraestrutura nova:**
- os `.ply` de D0–D3 estão no HD externo `/media/fabio/Seagate Expansion Drive/tcc-runs-arquivo/` (NTFS), em cópia única, verificada por hash;
- o fork está clonado no Mac em `~/code/etc/vksplatTCC`, na branch local `d4-rascunho`;
- execuções instrumentadas custam **~1 s por amostra**, porque a leitura de buffer é serial na CPU. Medir o custo antes de estimar prazo.

**Nenhum capítulo escrito.** Depósito em 06/nov.

---

> Esta é a seção a ler primeiro. O `CLAUDE.md` da raiz aponta para cá.
>
> **Nota de handoff (2026-09-25):** as entradas de 2026-09-22 a 2026-09-24 foram produzidas numa sessão paralela (fork da conversa principal, aberto para não sobrecarregar o contexto). A sessão principal não as viu. Tudo o que ela precisa está nesta seção e nas entradas datadas acima dela; nada relevante ficou só na conversa.

### Feito

- **Pré-registro estágio 1** commitado em `879dc8751e9c3d229506028600998840f24bb227`, cobrindo D0 a D3. **Desvio declarado** do teste estatístico em `aa79cf9`.
- **Escada de cinco degraus** implementada e travada em commits no fork `github.com/fabio-gabriel/vksplatTCC`, branch `tcc-base`, com tags `D0`–`D3`. SHAs em `pre-registro.md` §3.1.
- **120 execuções medidas:** N=30 em cada um de D0, D1, D2, D3. **Conferido por evidência em 2026-09-22** (contagem de diretórios, manifestos, `ambiente.json` e reexecução da análise).
- **H1 confirmada de forma categórica: 120 execuções, 120 hashes distintos.** Sobrevive a D1, o que elimina a explicação mundana do embaralhamento não semeado.
- **H2 sustentada** sobre D0: 9,0% dos pares com |ΔPSNR| ≥ 0,10 dB em N=30, contra critério de 5%. Margem reduzida frente a N=20 (14,2%); ver a entrada de 2026-09-22 para por que isso não é tendência.
- **Ambiente congelado em 2026-09-21** (`unattended-upgrades` e timers do apt mascarados). As 40 execuções de `run020`–`run029` são o primeiro bloco com ambiente registrado e homogêneo.
- **Custo do determinismo medido:** D3 é 14% mais lento que D2.
- Dados, manifestos de hash e logs versionados em `pivo-reprodutibilidade-3dgs/dados/<degrau>/`.
- **Plano completo de D4** em `pre-registro.md` §10, com o conjunto exato de mudanças.
- **Premissa de D4 confirmada no código** (2026-09-22): com o escalonamento desligado, `gs_renderer.cpp:345-346` fixa o backward em `pipeline_rasterize_backward[1]`, anotado `// per-splat backward`. Converter só `alphablend_shader_bwd_per_splat.slang` basta.
- **§10.7 passo 1 feito** (2026-09-23): magnitude dos gradientes e K medidos em D3, 3 repetições × 16 steps, zero NaN/Inf. **Cabe em `int32`** com escala por componente. Dados em `pivo-reprodutibilidade-3dgs/dados/gradientes/`. Escalas propostas na entrada de 2026-09-23.
- **§10.7 passo 2 feito** (2026-09-24): `slangc 2026.2.1` compila `InterlockedAdd` inteiro sobre `RWByteAddressBuffer` e emite **`OpAtomicIAdd` nativo**, sem emulação por compare-exchange; o ensaio dos 9 sítios gera exatamente 9 instruções. SHA-256 do asset registrado.
- **Semântica de estouro ancorada na especificação SPIR-V** (2026-09-24): adição inteira é módulo `2^N`, sem saturação. Bit-identidade de D4 não depende da escala; a escala só afeta qualidade.

### Onde estão as coisas (produzidas na sessão paralela)

| o quê | onde |
|---|---|
| medição de gradientes (não toca o fork) | `experimentos/medir_gradientes_d4.py` |
| teste da toolchain e das 6 variantes de atômico | `experimentos/testar_slang_atomic.sh` |
| inspeção de SPIR-V sem `spirv-tools` | `experimentos/inspecionar_spirv.py` |
| dados de gradientes, 3 repetições | `pivo-reprodutibilidade-3dgs/dados/gradientes/gradientes_rep0{0,1,2}.json` |
| toolchain Slang, **só na Ubuntu** | `~/opt/slang-2026.2.1/bin/slangc` (fora de `/usr/local`, nada via apt) |
| relatório e `.spv` do teste, **só na Ubuntu, não versionados** | `~/tcc-runs/slang-teste/` |
| teste de reprodução dos `.spv` do upstream (T0) | `experimentos/reproduzir_spv_upstream.py` — **não executado ainda**; saída a copiar para `pivo-reprodutibilidade-3dgs/dados/toolchain/` |
| adendo do estágio 2 | `pivo-reprodutibilidade-3dgs/pre-registro.md` §11, rascunho |
| clone do fork para leitura, **no Mac** | `~/code/etc/vksplatTCC` — tags `D0`–`D3` conferidas contra os `env.json` |

### Em andamento

- **Nada executando.** Decisão de 2026-09-22 mantida: não ampliar D0–D3; o tempo de máquina vai para D4.

### Caminho crítico — D4, agora desbloqueado

Estado de `pre-registro.md` §10.7:

| passo | estado |
|---|---|
| 1. medir gradientes e K | **feito** 2026-09-23 |
| 2. verificar SPIR-V de `InterlockedAdd` inteiro | **feito** 2026-09-24 |
| 3. fixar escalas e **commitar o adendo do estágio 2** | **feito.** §11.1–§11.9 em `02722af` (2026-09-25); T0 com 41/41 idênticos, caminho A, JSON em `2f2ad65`; §11.10, com o resultado e a vinculação, redigido em 2026-09-30 **e ainda não commitado** |
| 4. implementar (4 arquivos Slang, zero C++), commitar como D4, registrar SHA | **feito.** D4 = `22560858b0f2…`, V1–V4 passados, conferido de forma independente; SHA no §11.11, que precisa estar **commitado** antes da série |
| 5. rodar a série, verificar bit-identidade por hash | **feito** 2026-09-30, `de8693f`. **H3.4 refutada**: 10/10 hashes distintos. Dispersão muito reduzida, divergência só a partir do evento de densificação 129/144, e qualidade −0,39 dB. Ver a entrada de 2026-10-01 |

**O adendo (§11) contém, e dois itens mudaram em relação ao plano anterior:**

1. as nove escalas por componente, recalculadas dos JSON, com `round` ao mais próximo **e `clamp` por termo em ±2147483520**;
2. ~~`-fp-mode precise`, `-denorm-mode-fp32 preserve`~~ **CORRIGIDO: opções idênticas às do upstream** (`-O -fp-mode fast -line-directive-mode none`). Os `.spv` do upstream não declaram `float_controls`, e fixar `preserve` mudaria o binário por uma segunda razão. O modo de denormais fica declarado como limitação;
3. desvio D-1: ponto de leitura;
4. desvio D-2: medição em D3;
5. desvio D-3: escalas fixadas depois da dispersão de D0–D3;
6. ~~proibir `clamp`/`min`/`max` antes do atômico~~ **CORRIGIDO (D-4): exigir `clamp` por termo**, porque `OpConvertFToS` fora do range é comportamento indefinido, e **proibir saturação do acumulador**;
7. `int` direto;
8. dependência D2 → D4;
9. **novo:** teste T0 e caminhos A/B, com controle D3c pré-registrado para o caminho B;
10. **novo:** `config.slang`, `utils.slang` e `compile_shaders.py` intocados; invariante V2 sobre o diff D3 → D4.

**Riscos que continuam abertos:**

- **Execução no RADV não verificada.** Compilar não é executar; só a série de D4 responde.
- **Termos individuais do acumulador não medidos**, só o acumulado. Tolerável porque a aritmética é modular; deixaria de ser se o wraparound não valer na execução real.
- Não se verificou se a especificação **Vulkan** restringe algo sobre a semântica SPIR-V de adição inteira.

### Defeito de dados conhecido — declarar, não corrigir

**D3 não é série homogênea:** três estratos de ambiente, dez execuções cada (kernel −30/boot −1/libc 8.8; −31/boot 0/libc 8.8; −31/boot 0/libc 8.9). D0, D1 e D2 têm dois estratos (20 + 10). **O Mesa/RADV foi o mesmo nas 120.** O dano não atinge as hipóteses sustentadas: H2 repousa em D0, H1 é imune por construção, e a heterogeneidade afeta as H3.x, nenhuma das quais se sustentou. **Restringir D3 a um estrato homogêneo está proibido sem desvio declarado**, por ser o recorte favorável. Detalhes nas entradas de 2026-09-21 e 2026-09-22.

`run_degree.sh` e `coleta_serie.sh` gravam e coletam `ambiente.json` por execução desde 2026-09-21. **D4 deve rodar com esse registro ativo e sob o ambiente congelado.**

### Não estabelecido, e é limitação a declarar

- **Nenhuma H3.x sustentada em N=30, e o resultado andou para trás.** O Fligner de D0 vs D3 **deixou de rejeitar** ao passar de N=20 (p = 0,034) para N=30 (p = 0,0548), e a razão de IQRs subiu de 0,422 para 0,631 — o efeito aparente encolheu. **A projeção de N=50 está refutada:** excluir 1,0 exigiria **N ≈ 95 por degrau**, cerca de 90 h de máquina, inviável até 06/nov. **Decisão: não ampliar mais D0–D3; o tempo vai para D4.** As H3.x serão reportadas como não estabelecidas por limitação de poder, com o N necessário calculado.
- **A variabilidade da própria medida de dispersão é da ordem do efeito buscado.** Em blocos de N=10 do mesmo degrau, o IQR de D3 vai de 0,0131 a 0,0477 (3,6×), e D1 no bloco 1 tem IQR maior que D0 no bloco 1, invertendo a ordenação que o desenho mede. É achado por si — a medida de reprodutibilidade não é reprodutível — e é a razão de fundo da falta de poder.
- **H2 sustentada pelo critério (9,0% ≥ 5%), com margem reduzida.** O IC 95% bootstrap da fração é `[0,9% – 18,6%]` e **não** exclui 5%. O IC **não é o critério pré-registrado** e não pode ser tratado como tal; entra como declaração de incerteza.
- **Anomalia de D2 dissolvida:** a razão de IQR D1→D2 caiu de 1,335 (N=20) para 1,102 (N=30), comportamento de ruído. Não exige mais explicação física; reportar como episódio.

### Pendência institucional

**O Prof. Gilvan não havia sido informado de nenhum dos quatro reenquadramentos.** Em 2026-09-22 o aluno relatou estar "se organizando com o professor Gilvan". **Não há registro de que a conversa tenha ocorrido nem do que foi decidido** — confirmar com o aluno e registrar aqui. Até lá, continua sendo o risco mais malcoberto do projeto.

### Documentos desatualizados em relação a este caderno

Não corrigidos na sessão paralela, para não editar fonte de verdade sem o aluno:

- **`CLAUDE.md` da raiz** manda ler a seção "Estado em **2026-09-09**" — o nome desta seção mudou duas vezes desde então.
- **`pivo-reprodutibilidade-3dgs/PLANO.md` §9** é "Estado atual (**2026-09-09**)": ainda diz 80 execuções, H2 a 14,2%, e D4 bloqueado pela toolchain.
- **`PLANO.md` §2.1.1, §2.1.5 e §2.5**: ver pendência de texto 1 abaixo.
- **`pre-registro.md` §10**: é rascunho travado; as correções entram pelo adendo do estágio 2, **não por edição**.

### Pendências de texto

**Prioridade alta, criada em 2026-09-21 pela busca de originalidade:**

1. **Reescrever `PLANO.md` §2.1.1, §2.1.5 e §2.5** — a afirmação de que o fenômeno não foi quantificado caiu, e o posicionamento face ao NerfBaselines deixou de ser honesto para a v2.
2. **Resolver o protocolo de seed do NerfBaselines v2.** Decide a reivindicação de isolamento a seed fixa. Caminhos: perguntar a Jonáš Kulhánek, ou inspecionar o *runner* no código aberto.
3. **Acrescentar NerfBaselines e FreeTimeGS++ ao fichamento** — hoje com zero ocorrências lá. Sugerido eixo novo, "trabalhos que reportam dispersão".
4. **Monitorar arXiv:2605.03337 até o depósito.** A deriva v1→v3 vai na direção da tese deste TCC.
5. **Reverificar as citações literais** da issue #2996 e do PR #970 — são de peso no Cap. 2 e não foram reconferidas em fonte primária nesta sessão.
6. Conferir se `percent_dense=1e-5` está mesmo na issue #89; se não, remover o número do `PLANO.md` §2.1.3.

**Anteriores:** acrescentar Efron e Tibshirani ao fichamento (o bootstrap não se ancora em Hoefler e Belli). Decidir formato ABNT para citar comentário de issue de repositório. Survey `Advanced3DGS` **não localizado nem refutado** — pode ser que a anotação do fichamento esteja errada.

**Fechada em 2026-09-24:** SHA-256 do asset da Slang = `c2a05fa8643d45acf4662d7d18925ee239b16ba934da310c6cfece77dafe1927`.

**Nenhum capítulo escrito.**

### O que NÃO pode ser afirmado

- Que o trabalho **descobre** o não-determinismo. Kerbl o reconheceu em issue pública em 2023; um mantenedor do nerfstudio o atribuiu a atômicas de ponto flutuante em 2024. A contribuição é **quantificação e atribuição**.
- Que o tema é **inédito**. A busca de originalidade está incompleta.
- Que `-fp-mode fast` "autoriza reassociação" — a documentação do Slang não diz isso.
- Que Ubuntu 26.04 está fora da matriz do ROCm. É falso, e já custou uma reinstalação de sistema.
- Que os 20 runs de **D3** são execuções nominalmente idênticas entre si. **Não são:** D3 tem três estratos de ambiente (kernel −30/boot −1/libc 8.8; −31/boot 0/libc 8.8; −31/boot 0/libc 8.9), dez execuções em cada. D0, D1 e D2 têm dois estratos, 20 + 10.
- Que a atualização de kernel entre os blocos de D3 **alterou** a dispersão — nem que **não** alterou. N=10 por bloco não decide, e a comparação de blocos mostra que o estimador de dispersão oscila 3,6× entre blocos do mesmo degrau.
- Que o **Mesa/RADV** mudou em algum momento das 120 execuções. **Não mudou** — `dpkg.log` não registra nenhuma transação de `mesa-*`, `libvulkan*`, `libdrm*` ou `libgl*` na janela, o inventário de 2026-08-25 ancora `mesa-vulkan-drivers 25.2.8-0ubuntu0.24.04.2`, e os 40 `ambiente.json` novos confirmam a mesma versão.
- Que a atualização de `libc6` de 2026-09-21 06:36 afeta as métricas. É **hipótese plausível** pela libm no caminho do PyTorch de CPU, e não foi testada.
- Que a queda de H2 de 17,8% para 9,0% é **tendência**. Não é: comparando blocos de N=10 igual, D2 vai de 0,0% a 17,8% e volta a 0,0% dentro do mesmo degrau. O estimador é muito ruidoso, e 9,0% em N=30 é a melhor estimativa, não o fim de uma queda.
- Que **D3 reduz a dispersão** de forma estabelecida. Nenhuma H3.x se sustenta em N=30, e o efeito aparente encolheu em relação a N=20.
- Que as 80 primeiras execuções correram sob ambiente congelado. **O congelamento é de 2026-09-21 e não retroage.** As 40 de `run020`–`run029` correram sob ambiente congelado e homogêneo.
- Que o fenômeno **nunca foi quantificado publicamente**. Caiu em 2026-09-21: NerfBaselines v2 reporta σ sobre quatro treinos independentes de 3DGS e gsplat no Mip-NeRF 360; FreeTimeGS++ v3 reporta média ± σ sobre dez execuções.
- Que **todo trabalho que reporta dispersão varia a seed**. **Indeterminado.** O protocolo de seed do NerfBaselines v2 não é declarado, e a v1 afirmava fixar seeds.
- Que **nenhum trabalho isola o não-determinismo**. FreeTimeGS++ isola a inicialização explicitamente: *"we fix the initialization and repeat optimization under the same protocol."*
- Que *"eles mostraram que o protocolo compromete a comparabilidade; este trabalho mostra que, mesmo com protocolo idêntico, a execução também compromete"*. **Não vale para a v2 do NerfBaselines, que mostra as duas coisas.** Reescrever `PLANO.md` §2.1.5.
- Que FreeTimeGS++ se distingue deste TCC nas quatro dimensões pretendidas **na formulação forte**. Objeto, causa e intervenção sustentam-se; a dimensão de seed está **estreitada** e precisa ser redigida como "seed fixa × seed variável com inicialização fixa".
- Que `percent_dense=1e-5` consta do corpo da issue #89. **Contestado e não reconferido.**
- Que **a especificação SPIR-V diz que `OpAtomicIAdd` faz wraparound**. Ela diz que `OpAtomicIAdd` faz *"integer addition"*, e que `OpIAdd` produz os *"low-order N bits"*. A conclusão é composição de duas cláusulas; redigir assim.
- Que **D4 funciona**. Compila e emite a instrução certa; **nunca foi executado**.
- Que **D4 elimina a dependência de `VK_EXT_shader_atomic_float`**. Elimina **no shader `per_splat`**; as outras variantes de backward e `morton_sort.slang` continuam exigindo a extensão.
- Que **o acumulador nunca estoura**. Só o gradiente acumulado foi medido, não os termos; e o máximo observado em 3 execuções não é o máximo possível.
- Que a medição de gradientes usou a estratégia de instrumentação X. **Não se sabe** qual das duas ficou ativa: o script não a gravava no JSON e o terminal foi perdido. Corrigido para execuções futuras.
- Que **a conversa com o Prof. Gilvan ocorreu**. Não há registro.
- Que **D0–D3 e D4 foram compilados pelo mesmo compilador**. D0–D3 executaram os `.spv` do upstream, de versão de Slang desconhecida (`generator` versão 0). D4 será compilado pelo nosso `slangc 2026.2.1`. Só T0 diz se os bytes coincidem.
- Que **`clamp` antes do atômico quebra a associatividade**. `clamp` **por termo** não quebra, e é exigido para evitar o comportamento indefinido de `OpConvertFToS`. O que quebra é saturar o **acumulador**.
- Que **o modo de denormais foi controlado** em algum degrau. Não foi: é *"implementation defined"* nos cinco, por decisão de não alterar as opções do upstream.
- Que **D4 produz execuções bit-idênticas**, ou que é "quase determinístico" num sentido formal. São 10 hashes distintos em 10, e H3.4 está refutada pelo critério pré-registrado.
- Que **a perda de 0,39 dB de D4 é o custo do determinismo**. A hipótese mais provável, ainda não testada, é que a escala da cônica zera quase todo o gradiente de covariância.
- Que **a fonte residual de não-determinismo é X**. Não foi identificada. Sabe-se só que é rara e tardia: as 10 execuções coincidem em 129 dos 144 eventos de densificação.
- Que **a redução de dispersão D3→D4 se deve só à acumulação inteira**. Passa no §5.2, mas há confundidor aberto: em D4 o gradiente de cônica é quase todo zerado. Só o D4b separa os dois efeitos.
- Que **as execuções de D4 diferem só na ordem das gaussianas**. Não é permutação: ~99% das gaussianas diferem em valor, alinhadas por índice.
- Que **se sabe quando a divergência de D4 começa**. Densificação idêntica até o evento 129 não implica parâmetros bit-idênticos até lá.
