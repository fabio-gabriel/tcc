# Plano do TCC: Renderização Neural em Hardware Heterogêneo

> Documento vivo: estado, cronograma, sprints, TODOs e decisões. Atualizar a cada sprint encerrado ou quando uma decisão importante for tomada. Para o papel de Claude e convenções estáveis do projeto, ver `CLAUDE.md`. Para fontes verificadas do experimento, ver `bibliografia/verificacao-experimento-rdna4.md` (versionado no repositório; substitui a memória persistente `reference_experimento_rdna4.md`, perdida em reinstall do Claude em 2026-08-06).
>
> **Título completo do trabalho em §1.** O enquadramento científico está em **§2 — esta é a fonte de verdade** em caso de divergência com qualquer outro arquivo.

## 1. Identidade

| Item | Valor |
|---|---|
| Aluno | Fabio Gabriel |
| Curso | Engenharia de Computação, UFC |
| Orientador | Prof. Gilvan |
| Tipo | Monografia bibliográfica + experimento próprio |
| Norma de formatação | ABNT (NBR 6023, 10520, 14724) |
| Formato de trabalho atual | Markdown (`.md`); migração futura para LaTeX (`abntex2`) |
| Início efetivo do projeto | 2026-06-23 |
| **Janela de execução (redefinida em 2026-08-20)** | **24/ago/2026 → 06/nov/2026** — 75 dias corridos, **10 semanas e 5 dias** |
| **Depósito** | **06/nov/2026** (sexta-feira) — confirmado pelo aluno em 2026-08-20 |
| Defesa | posterior ao depósito, data a definir — **fora** da janela de execução acima |

### Título

**Título de trabalho (definido em 2026-08-20):**

> **Renderização neural em hardware heterogêneo: decomposição do custo de desempenho de backends agnósticos de fornecedor**

**Título em inglês (para o *abstract*, NBR 14724):**

> Neural rendering on heterogeneous hardware: decomposing the performance cost of vendor-agnostic backends

**Título alternativo** (formulação anterior ao reenquadramento de §2, mantida como registro e como opção de retorno):

> Renderização Neural em Hardware Heterogêneo — Portabilidade e desempenho de NeRF/3DGS em GPUs AMD RDNA 4 (RX 9070 XT)

Racional da escolha:

- **Preserva o título principal já validado pelo Prof. Gilvan** ("Renderização neural em hardware heterogêneo"), mudando apenas o subtítulo. O objeto não mudou; o recorte ficou mais preciso
- **"Decomposição" sinaliza análise, não benchmarking** — responde diretamente à crítica que motivou o reenquadramento (§2)
- **"Custo de desempenho" nomeia o objeto sem prometer magnitude**, e portanto não envelhece a cada release de driver
- **Omite deliberadamente** "AMD vs NVIDIA" / "CUDA vs ROCm" (é o enquadramento de comparação de produtos que foi abandonado), "RDNA 4" / "RX 9070 XT" (sob o novo enquadramento o hardware é estudo de caso, não objeto) e "3D Gaussian Splatting" (risco de execução: se o VkSplat não subir em RDNA 4 e o trabalho recair sobre Taichi/NeRF, o título continua verdadeiro)


## 2. Enquadramento científico (reformulado em 2026-08-20)

> **Motivação da reformulação.** O enquadramento anterior — "medir o gap CUDA × não-CUDA em 4 dimensões" — produzia um relatório de benchmarking, não uma contribuição científica. Duas fragilidades concretas: (a) a comparação original fazia variar **três fatores ao mesmo tempo** (hardware, backend e implementação), tornando qualquer diferença observada inatribuível; (b) as hipóteses afirmavam *magnitude* ("existe gap de X%"), que envelhece a cada release de driver, em vez de *mecanismo*, que generaliza. A crítica de "falta de produção de ciência", levantada por um segundo professor, procede contra o desenho anterior e é endereçada aqui.

### Pergunta de pesquisa

> **Qual é o custo de desempenho de adotar backends agnósticos de fornecedor (Vulkan, Taichi) em lugar de CUDA nativo em pipelines de renderização neural, e como esse custo se distribui entre os estágios do pipeline?**

Sub-perguntas:

1. O gap total observado entre uma execução CUDA nativa e uma execução em backend portátil pode ser **decomposto** em contribuições separáveis de hardware, backend e implementação?
2. O custo de abstração é **uniforme** ao longo do pipeline, ou concentra-se em estágios com padrão de acesso irregular (ordenação, operações atômicas) frente a estágios dominados por GEMM densa?
3. Qual a defasagem entre **suporte declarado** e **suporte efetivo** no stack de compute aberto (ROCm) para GPUs RDNA de consumo?

### Hipóteses (orientadas a mecanismo, não a magnitude)

Cada hipótese abaixo declara explicitamente **o que a falsificaria** — critério ausente na versão anterior.

- **H1, heterogeneidade do custo de abstração.** O custo de adotar um backend agnóstico de fornecedor **não é uniforme** ao longo do pipeline de 3DGS: concentra-se nos estágios dominados por ordenação e operações atômicas (tile binning, composição alpha) e é substancialmente menor nos estágios dominados por GEMM densa.
  - *Falsificação:* se o overhead relativo por estágio for aproximadamente constante (dentro da variância medida), H1 é falsa e o custo de abstração é um fator multiplicativo global.
- **H2, decomposição fatorial.** O gap total entre `gsplat`(CUDA)@NVIDIA e `VkSplat`(Vulkan)@AMD decompõe-se de forma aproximadamente separável em efeito de hardware, efeito de backend e efeito de implementação, estimáveis por contrastes **intra-máquina**.
  - *Falsificação:* se a soma dos contrastes intra-máquina não reconstruir o gap total dentro da variância, existe interação não modelada entre os fatores — o que é resultado positivo e deve ser caracterizado, não descartado.
- **H3, energia como função do backend.** Na **mesma** máquina e mesmo dataset, a energia por treinamento varia entre backends de forma não proporcional ao tempo de execução — isto é, o backend altera a eficiência energética além do que a diferença de tempo explica.
  - *Falsificação:* se J/treinamento for aproximadamente proporcional ao tempo em todos os backends, H3 é falsa e a energia não acrescenta informação sobre o tempo.
- **H4, assimetria do suporte declarado × efetivo.** A defasagem entre suporte declarado (matriz oficial do fornecedor) e suporte efetivo (o que compila, roda e produz resultado correto) no stack ROCm é **estruturalmente assimétrica** entre CDNA (datacenter) e RDNA (consumo), e não se reduz monotonicamente com o tempo.
  - *Falsificação:* se, ao longo da janela de observação, os indicadores de defasagem em RDNA convergirem para os de CDNA, H4 é falsa.

### Hierarquia de afirmações (por força de evidência)

Decisão metodológica central: **não tentar blindar a comparação cross-vendor** — ela é inblindável (host de nuvem não-controlado, código distinto dos dois lados, drivers distintos). Em vez disso, hierarquizar:

| Nível | Afirmação | Controle | Depende de |
|---|---|---|---|
| **Principal** | Custo do backend portátil frente ao nativo, **na mesma máquina**, mesmo dataset, mesmo commit | Total — apenas o backend varia | Uma máquina funcionando |
| **Secundária** | Efeito do hardware com implementação constante (mesmo binário Vulkan em duas GPUs) | Parcial — host difere | Acesso às duas GPUs |
| **Exploratória** | Comparação cross-vendor agregada (CUDA@NVIDIA × Vulkan@AMD) | Baixo — três fatores variam | Execução pareada completa |
| **Bibliográfica** | H4, suporte declarado × efetivo | N/A — evidência documental datada | Nenhuma execução |

Consequência prática: **se o eixo cross-vendor desabar, o TCC permanece de pé** sobre o nível principal e o bibliográfico. O risco de naufrágio por falha de bring-up deixa de existir.

## 3. Caminho experimental escolhido

O experimento é um **desenho fatorial**: em vez de comparar dois produtos, faz variar um fator por vez para permitir atribuição causal. Executa baselines existentes sob condições controladas e mede as 4 dimensões.

### Desenho fatorial (backend × hardware)

A célula decisiva é a **coluna da 5070 Ti**: ali o hardware é constante e apenas o backend varia, isolando o custo de abstração. Essa é a única comparação sob controle total, e é onde reside a afirmação principal do TCC.

| Implementação / backend | RTX 5070 Ti (nuvem) | RX 9070 XT (bancada) | Contraste que habilita |
|---|---|---|---|
| `gsplat` — CUDA nativo | ✅ | — (por definição) | âncora "nativo" |
| `VkSplat` — Vulkan compute | ✅ | ✅ | **custo do backend** (vs `gsplat`, mesma máquina); **efeito do hardware** (mesmo binário, duas GPUs) |
| `taichi-ngp-renderer` → CUDA | ✅ | — | custo do backend dentro da DSL |
| `taichi-ngp-renderer` → Vulkan | ✅ | ✅ | idem, e replicação do contraste em segundo pipeline |

Contrastes derivados:

- `VkSplat`@5070 **vs** `gsplat`@5070 → custo puro do backend portátil, hardware constante
- `VkSplat`@9070 **vs** `VkSplat`@5070 → efeito do hardware, implementação constante
- Taichi→CUDA **vs** Taichi→Vulkan, mesma máquina → custo do backend dentro de uma mesma DSL
- Composição dos três → teste de H2 (separabilidade dos fatores)

### Pré-registro do protocolo

**Compromisso metodológico:** o Cap. 4 (protocolo, N de rodadas, critério de PSNR-alvo, versões fixadas, definição de sucesso e de descarte de rodada) é escrito e **commitado em git antes** da execução do Sprint 3. O histórico do repositório passa a servir como evidência de que o protocolo não foi ajustado aos resultados. Custo próximo de zero, ganho de credibilidade alto na defesa — e endereça diretamente a crítica de rigor experimental.

### Lado CUDA (RTX 5070 Ti alugada em vast.ai, CUDA 13.X)

| Pipeline | Implementação de referência |
|---|---|
| Instant-NGP | `NVlabs/instant-ngp` (oficial, CUDA + tiny-cuda-nn) |
| 3D Gaussian Splatting | `graphdeco-inria/gaussian-splatting` (oficial, CUDA) |
| 3DGS alternativo | `nerfstudio-project/gsplat` (CUDA mais modular) |

### Lado não-CUDA (RX 9070 XT, RDNA 4)

| Pipeline | Rota concreta | Tipo | Papel no desenho reformulado |
|---|---|---|---|
| 3DGS via Vulkan compute | `harry7557558/vksplat` (Chen, Ibrahim & Liu, 2026; validar em Sprint 0) | Vulkan | **Caminho crítico.** Sustenta a afirmação principal e a secundária |
| Instant-NGP via Taichi | `Linyou/taichi-ngp-renderer` com backend Vulkan | Taichi/Vulkan | **Caminho crítico.** Replica o contraste em segundo pipeline; cobre H1 se VkSplat não subir |
| 3DGS via HIP | Branch do PR `graphdeco-inria/gaussian-splatting#1297` | ROCm/HIP | **Corte candidato.** Depende de ROCm (bloqueado, ver §8); PR parado há ~8 meses |
| Baseline genérico de treino | PyTorch + ROCm 7.x + Nerfstudio/Nerfacto | ROCm | **Rebaixar.** Vira *tentativa de instalação documentada* — evidência de H4, não experimento de desempenho |
| Talvez? | `ZJLi2013/tiny-rocm-nn` (renomeado/transferido de `PhysicalAI-AIM/tiny-rocm-nn`, confirmado 2026-08-06; CDNA 3/MI300X → adaptar WMMA RDNA) | HIP/WMMA | **Corte candidato.** Escopo de trabalhos futuros |

> **Nota sobre o papel do ROCm no enquadramento reformulado.** ROCm deixa de ser rota experimental obrigatória e passa a ser **objeto de análise documental** (H4): matriz de suporte, os 5 bugs gfx1201 rastreados, descompasso PyTorch 7.2 ↔ ROCm 7.14, restrição de SO. Esse material já está verificado em `bibliografia/verificacao-experimento-rdna4.md` e sustenta H4 **sem depender de nenhuma instalação bem-sucedida**. Uma instalação que falhe é dado, não fracasso.


### Métricas, operacionalizadas em 4 dimensões

**Performance**
- **Decomposição por estágio do pipeline** (projeção → tile binning/ordenação → rasterização/composição alpha → backward). **Esta é a medição que torna H1 testável**; sem ela o TCC volta a ser cronometragem de tempo total. Instrumentar por marcadores de tempo no código e/ou profiler (Radeon GPU Profiler para Vulkan; Nsight do lado CUDA)
- Tempo de treinamento até atingir PSNR-alvo (ex.: PSNR ≥ 30 dB no dataset Synthetic-NeRF; PSNR ≥ 27 dB no Mip-NeRF 360)
- FPS de inferência (renderização) em resolução 800×800 e 1920×1080
- (Opcional) throughput de operações fundamentais: GEMM FP16, hash lookup
- Reportar **distribuição**, não média nua: N ≥ 3 rodadas, com média, desvio padrão e intervalo de confiança. Não reportar *speedup de médias* sem indicar dispersão (ver Eixo E do fichamento, item de metodologia de benchmarking científico)

**Portabilidade**
- Tempo até conseguir configurar o pipeline (horas até primeiro treino bem-sucedido)
- Inventário de bugs/issues encontrados (linkar issues upstream relevantes)
- Cobertura de operadores PyTorch+ROCm vs CUDA (script comparando outputs dos operadores comuns ao Nerfstudio)
- Tamanho de patch necessário (LOC modificadas) sobre upstream para fazer rodar em RDNA 4
- Taxa de sucesso de instalação (instala no primeiro try? quantas tentativas?)

**Eficiência energética**
- **Afirmação principal de H3 é intra-máquina:** comparar backends na *mesma* GPU, mesmo sensor, mesmo dataset. Essa comparação é blindável. A comparação energética cross-vendor permanece exploratória, com as ressalvas abaixo
- Potência instantânea durante treinamento e inferência via amostragem `rocm-smi --showpower` (AMD) e `nvidia-smi --query-gpu=power.draw` (NVIDIA), intervalo ≤ 1 s
- Energia total por treinamento (Wh) e energia por imagem renderizada (J/frame), por integração das amostras
- Reportar potência média, pico, desvio padrão; integrar para energia
- **Restrição metodológica (2026-08-06):** como o lado NVIDIA roda em host de nuvem não-controlado, H3 limita-se a **potência de placa** (telemetria interna da GPU), nunca a energia do sistema completo; registrar também temperatura da GPU, que afeta clocks e portanto potência
- Calibrar instrumentação no Sprint 0 (validar se `rocm-smi` reporta corretamente em RDNA 4; há issues conhecidas em gerações antigas; validar também `nvidia-smi` dentro do container da vast.ai)
- **Achado do inventário de 2026-08-18 (revisa o "plano B"):** a via `sysfs` já reporta potência sem ROCm — `/sys/class/drm/card1/device/hwmon/hwmon5/power1_average` retornou 26 W em idle, valor não-redondo (critério do próprio script para descartar sensor não implementado). O gate de H3 é atendível **sem `rocm-smi` e sem wattímetro externo**. A tabela de gates do inventário marcou "NAO" por avaliar apenas a via `rocm-smi`, ignorando o fallback que ela mesma coletou com sucesso

**Suporte declarado × suporte efetivo (H4) — não-experimental, predominantemente bibliográfico + GitHub mining**

> Eixo **independente de execução**: sustenta-se inteiramente em evidência documental datada e sobrevive a qualquer falha de bring-up. Boa parte já está coletada em `bibliografia/verificacao-experimento-rdna4.md`.

- **Indicador de assimetria CDNA × RDNA** (o que torna H4 falsificável): para cada componente do stack, registrar se o suporte a arquitetura de datacenter e o suporte a arquitetura de consumo estão no mesmo estágio de maturidade — ex.: `tiny-rocm-nn` validado em CDNA 3 e não em RDNA 4; backend AMDGPU do Taichi presente no código e ausente da matriz pública de plataformas; rocWMMA declarando gfx1200/1201 sem port de MLP fundido correspondente
- Tabela cronológica: técnicas relevantes 2020-2026 (NeRF, Instant-NGP, 3DGS, Mip-NeRF 360, Zip-NeRF, Nerfacto, etc.) com datas de lançamento CUDA × datas de lançamento de equivalente não-CUDA acessível, e gap em meses
- Inventário de bibliotecas: cuBLAS↔rocBLAS, cuDNN↔MIOpen, NCCL↔RCCL, tiny-cuda-nn↔(nada para RDNA), CUTLASS↔Composable Kernel, NVTX↔ROCTracer
- Análise quantitativa: número de issues abertas em `pytorch/pytorch` e `ROCm/ROCm` específicas de gfx1201 vs número total de issues; tempo médio de resolução
- **Observação longitudinal:** o rastreamento dos 5 bugs gfx1201 já cobre a janela jun→ago/2026. Reamostrar antes do depósito produz uma série temporal — evidência mais forte que um retrato único

### Bugs ativos relevantes em PyTorch + ROCm gfx1201 (verificados em 2026-06-23; status reconfirmado em 2026-08-06 — detalhe em `bibliografia/verificacao-experimento-rdna4.md`)
- `pytorch/pytorch#177834`: LSTM/MIOpen incorreto em gfx1201 — **ainda aberto**
- `pytorch/pytorch#187343`: `expandable_segments:True` causa `hipErrorIllegalAddress` — **fechado `not_planned`** (engenheiro AMD não conseguiu reproduzir em gfx1201; não é fix confirmado)
- `pytorch/pytorch#181939`: falha CMake `gfx1036;gfx1201` — **ainda aberto**
- `ROCm/ROCm#6116`: `torch.mm` produz NaN com >~500K linhas — **fechado `completed`, mas por inatividade**; o próprio autor relatou que o bug ainda reproduz no driver 26.2.2 e só "parece resolvido" no Adrenalin 26.3.1 — tratar como mitigação de driver não confirmada, não como fix do ROCm
- `ROCm/ROCm#6374`: page fault OpenCL/ROCr em RDNA 4 (XNACK off, host-VA) — **ainda aberto**

Esses bugs são parte do achado empírico do TCC (Cap. 5, discussão de portabilidade e maturidade do stack). Apenas 1 dos 5 tem indício de mitigação, e mesmo esse é ambíguo — reforça a tese de imaturidade do stack ROCm em RDNA 4 no curto prazo (jun→ago/2026).

## 4. Cronograma: fases e marcos

**Janela recalculada em 2026-08-20: 24/ago → 06/nov/2026.** São **10 semanas e 5 dias** (75 dias corridos), contra as 17 semanas do cronograma original — uma compressão de ~35%. O calendário abaixo cai em semanas de segunda a domingo; `24/ago` é segunda e `06/nov` é sexta.

**`06/nov` é a data de DEPÓSITO** (confirmado pelo aluno em 2026-08-20), não de defesa. Três consequências:

- A janela de 10 semanas e 5 dias está **integralmente disponível para escrita e experimento** — não há antecipação oculta de prazo. Era o cenário melhor entre os dois possíveis
- **A monografia precisa estar completa e formatada em ABNT em 06/nov.** Depósito é a versão que vai à banca: não existe "terminar depois"
- **Preparação de defesa e eventuais correções pós-banca ficam após 06/nov**, fora desta janela — e por isso saem do Sprint 5, que já está no limite

| Fase | Sem | Período | Saída | Status |
|---|---|---|---|---|
| **Sprint 0: Viabilidade** | 1 | 24/ago → 30/ago | Rota Vulkan roda ≥ 1 cena; instrumentação validada; decisão go/no-go por pipeline | Parcial (git e inventário feitos; bring-up não) |
| **1: Cap. 2 + leituras-núcleo** | 2-3 | 31/ago → 13/set | Sumário ABNT; Cap. 2 escrito; Eixo E validado e lido | Não iniciado |
| **2: Cap. 3 + Cap. 4 + protocolo** | 4-5 | 14/set → 27/set | Cap. 3 escrito; **Cap. 4 escrito e commitado (pré-registro)**; dataset e métricas fixados | Não iniciado |
| **3: Experimento principal** | 6-8 | 28/set → 18/out | Execuções concluídas; dados brutos em CSV/JSON no repo | Não iniciado |
| **4: Cap. 5 + Cap. 6 + revisão** | 9-10 | 19/out → 01/nov | Resultados/discussão e conclusão escritos; revisão de Cap. 2-4 | Não iniciado |
| **5: Fechamento** | 11 | 02/nov → 06/nov | Cap. 1, resumo/abstract, revisão integral, **depósito em 06/nov** | Não iniciado |
| *(pós-janela)* | — | após 06/nov | Preparação da defesa; correções pós-banca | — |

### Consequências da compressão — ler antes de planejar qualquer semana

1. **Os "cortes candidatos" de §5 deixam de ser opcionais.** Em 17 semanas eram avaliáveis; em 11 são o que torna o plano executável. Tratar como escopo-base e reincorporar item a item apenas se houver folga real.
2. **Cap. 4 (Metodologia) migra do Sprint 4 para o Sprint 2.** Não é escolha de conveniência: o pré-registro (§3) exige o protocolo escrito e commitado **antes** da execução. O efeito colateral é bom — alivia o fim do cronograma, que era onde a compressão mais doía.
3. **Cap. 6 (Conclusão) migra para o Sprint 4**, junto do Cap. 5, enquanto os resultados estão frescos.
4. **Sprint 5 tem 5 dias úteis e não cabe mais que Cap. 1, resumo/abstract, revisão final e depósito.** Qualquer tarefa estrutural que sobrar para essa semana é risco direto ao depósito.
5. **A migração para LaTeX (`abntex2`) sai do Sprint 5.** Duas opções, decidir na semana 1: (a) montar o esqueleto `abntex2` já no Sprint 0 e escrever direto em LaTeX, evitando a migração; (b) manter `.md` e migrar no Sprint 4. A opção (a) é a mais segura — migrar formato a 5 dias do depósito é risco desnecessário.
6. **Não há margem para atraso dentro da janela.** O cronograma original embutia ~3 semanas finais de folga; agora não há nenhuma. Como `06/nov` é depósito, a banca e as correções vêm depois — mas isso não compra tempo de escrita: o texto tem de estar pronto na data.

> **Resolvido em 2026-08-20:** `06/nov` é **depósito**, confirmado pelo aluno. A janela permanece em 10 semanas e 5 dias, sem redução.

## 5. Sprints e TODOs

### Sprint 0: Viabilidade (semana 1: 24/ago → 30/ago/26)

Objetivo: validar antes de qualquer escrita que (a) a rota Vulkan roda, (b) a instrumentação de medição (potência, tempo, métricas de qualidade) funciona, (c) há clareza sobre o acesso a hardware NVIDIA.

> **Semana 1 é a mais carregada do cronograma** — a máquina não tem nada instalado (sem ROCm, PyTorch, Taichi, pip, gcc, cmake, glslc; Python 3.14.4 fora das faixas suportadas; 6/6 gates reprovados no inventário de 18/ago). Hard-cap sugerido: se a rota Vulkan não subir até o fim da semana, acionar os cortes e seguir para o Sprint 1 — a escrita não pode ficar bloqueada pelo bring-up.

- [x] Decidir hospedagem do repositório git — **GitHub** (`fabio-gabriel/tcc`, via alias SSH `github-personal`)
- [x] Inicializar `git init` no repositório — feito; primeiro commit em 2026-06-23, 4 commits em `main`, sincronizado com `origin`
- [ ] Configurar Tailscale entre Mac e máquina Linux (PAUSADO a pedido do usuário em 2026-06-23; retomar antes do bring-up)
- [ ] Validar pessoalmente o paper VkSplat (arXiv:2605.00219) e o repositório `harry7557558/vksplat`
- [x] Decisão sobre hardware NVIDIA: **RTX 5070 Ti alugada na vast.ai** (decidido 2026-08-06)
- [ ] Alugar instância vast.ai de teste (5070 Ti — disponibilidade já confirmada no catálogo em 2026-08-06): registrar especificações do host (CPU, RAM, lanes PCIe, disco), validar `nvidia-smi --query-gpu=power.draw` dentro do container
- [ ] Definir critérios de seleção de instância vast.ai (PCIe x16, CPU/RAM mínimos) e fixar imagem Docker por digest para reprodutibilidade
- [ ] Bring-up (lado AMD): rodar `Linyou/taichi-ngp-renderer` em uma cena
- [ ] Bring-up (lado AMD): rodar 3DGS via PR #1297 em uma cena
- [ ] Bring-up (lado AMD): rodar VkSplat em uma cena
- [ ] Bring-up (lado AMD): PyTorch + ROCm 7.x, tutorial mínimo (treino MNIST ou similar)
- [ ] Validar instrumentação de potência: amostragem `rocm-smi --showpower` em background durante uma execução; verificar se reporta valores plausíveis em RDNA 4
- [ ] Caderno de campo: registrar cada bug/quirk encontrado em arquivo versionado no repo
- [ ] Decisão go/no-go por pipeline; ajustar escopo se necessário

> **Cortes candidatos — Sprint 0** (avaliar, não executar às cegas)
>
> | Item | Ação sugerida | Justificativa |
> |---|---|---|
> | Bring-up 3DGS via PR #1297 | **Cortar** | Depende de ROCm, bloqueado pelo SO (§8); PR parado há ~8 meses, 1 commit, 0 comentários |
> | Bring-up PyTorch + ROCm 7.x | **Rebaixar** a tentativa documentada com limite de tempo (ex.: 4 h) | O resultado — mesmo negativo — é evidência de H4. Não é experimento de desempenho |
> | Bring-up `tiny-rocm-nn` | **Cortar** | Só validado em CDNA 3; adaptar WMMA para RDNA é TCC próprio. Vai para trabalhos futuros |
> | Validar potência via `rocm-smi` | **Substituir** pela via `sysfs`/hwmon | Já funciona sem ROCm (ver §3, achado de 2026-08-18); desacopla H3 do bloqueio de ROCm |
>
> **Reordenação do caminho crítico decorrente do reenquadramento:** Vulkan primeiro, ROCm depois (ou nunca). A pilha Vulkan é a única já parcialmente pronta na máquina — RADV e `libvulkan1` instalados, faltando `vulkan-tools` (para `vulkaninfo`) e `glslc`/`glslangValidator`. Não depende de ROCm, nem da restrição de SO, nem dos grupos `render`/`video`. Ordem sugerida: `vulkan-tools` + compiladores de shader → confirmar `VK_KHR_cooperative_matrix` → VkSplat → Taichi/Vulkan.

### Sprint 1: Cap. 2 + leituras-núcleo (semanas 2-3: 31/ago → 13/set/26)

Objetivo: produzir o capítulo de fundamentação teórica de renderização neural.

- [ ] Fixar pergunta de pesquisa final + hipóteses
- [ ] Definir sumário ABNT da monografia
- [ ] Ler papers prioritários do Eixo A do fichamento (NeRF, 3DGS, Instant-NGP, métricas, surveys)
- [ ] Escrever Cap. 2: Renderização Neural (representações implícitas, explícitas, volume rendering, splatting, métricas PSNR/SSIM/LPIPS)
- [ ] Continuar leituras dos Eixos B e C em paralelo
- [ ] **(novo)** Ler os itens do Eixo E do fichamento (métrica de portabilidade de desempenho, roofline, metodologia de benchmarking) — são a base teórica que o enquadramento anterior não tinha

> **Cortes candidatos — Sprint 1**
>
> | Item | Ação sugerida | Justificativa |
> |---|---|---|
> | Leituras do Eixo B (variantes) | **Cortar B.8–B.11** (Deformable 3DGS, 4DGS, Scaffold-GS, GaussianPro) | Nenhuma entra no experimento. Citar de passagem no Cap. 2 a partir dos surveys A.11 |
> | Eixo A completo | **Reduzir** ao núcleo A.1, A.6, A.7, A.8 + um survey (A.10 ou A.11, não os dois) | O Cap. 2 precisa fundamentar o que é medido, não varrer o campo |
> | Eixo D (datasets) | **Adiar** para o Sprint 2, junto da escolha do dataset | Ler dataset que não vai ser usado é custo puro |

### Sprint 2: Cap. 3 + Cap. 4 + protocolo pré-registrado (semanas 4-5: 14/set → 27/set/26)

> **Cap. 4 (Metodologia) foi antecipado para cá** (era Sprint 4). O pré-registro de §3 exige o protocolo escrito e commitado antes da execução — logo, o capítulo que o descreve nasce aqui, não depois dos resultados.

- [ ] Ler papers do Eixo C (Taichi, ROCm, HIP, Tensor Cores, WMMA, Davis et al. 2024 sobre performance portability)
- [ ] Escrever Cap. 3: Hardware Heterogêneo e Portabilidade (CUDA vs ROCm/HIP vs Vulkan vs Taichi; Tensor Cores vs WMMA; ecossistemas de bibliotecas)
- [ ] Selecionar datasets canônicos: Synthetic-NeRF + Mip-NeRF 360 + Tanks and Temples (a confirmar com Prof. Gilvan)
- [ ] Fechar protocolo experimental: número de rodadas, hardware, versões fixadas (`requirements.txt` / Dockerfile / SHAs), critérios de PSNR-alvo, intervalo de amostragem de potência, scripts de coleta
- [ ] Construir tabela cronológica de "gap funcional" (CUDA-release → equivalente acessível); esta tabela é entregável próprio do Cap. 3 ou Cap. 5
- [ ] Construir inventário de paridade de bibliotecas CUDA ↔ ROCm
- [ ] **(novo, decorre do reenquadramento)** Definir a instrumentação por estágio do pipeline — sem ela H1 não é testável. Decidir entre marcadores no código-fonte, profiler externo (RGP/Nsight), ou ambos
- [ ] **(novo)** **Escrever o Cap. 4: Metodologia** (protocolo, datasets, métricas, instrumentação, limitações) — antecipado do Sprint 4
- [ ] **(novo)** **Commitar o Cap. 4 e o protocolo antes de qualquer execução do Sprint 3** (pré-registro, ver §3). Lembrar o aluno: o commit é dele, e é o que dá valor probatório ao histórico
- [ ] **(novo)** Decidir a estratégia de LaTeX: esqueleto `abntex2` agora e escrita direta em LaTeX, ou `.md` com migração no Sprint 4 (ver §4, consequência 5)

> **Cortes candidatos — Sprint 2**
>
> | Item | Ação sugerida | Justificativa |
> |---|---|---|
> | 3 datasets | **Cortar para 1 principal:** Synthetic-NeRF | Leve, canônico, cabe em 124 GB de disco e 15 GiB de RAM. Mip-NeRF 360 entra como 2-3 cenas *se* couber |
> | Tanks and Temples | **Cortar** | Fonte primária ainda não validada (D.5); não acrescenta contraste ao desenho fatorial |
> | ScanNet++ / DTU MVS | **Cortar** | Só fariam sentido se o TCC avaliasse reconstrução de superfície, o que não é o caso |
> | Inventário de paridade de bibliotecas | **Reduzir** às linhas que entram na argumentação de H4 | Tabela exaustiva é enchimento; 5-6 linhas bem escolhidas sustentam a tese |

### Sprint 3: Experimento principal (semanas 6-8: 28/set → 18/out/26)

- [ ] **Lado AMD (todos):** executar 3DGS (PR #1297, VkSplat) e Instant-NGP (taichi-ngp-renderer) nos datasets selecionados, com rodadas para média/desvio
- [ ] **Lado AMD:** executar baseline PyTorch + ROCm em 1-2 tarefas comparáveis para complementar
- [ ] **Lado NVIDIA (RTX 5070 Ti, vast.ai):** executar Instant-NGP oficial e 3DGS oficial nos mesmos datasets, mesma instrumentação, mesmos critérios; registrar especificações do host e digest da imagem para cada sessão de aluguel
- [ ] **Lado NVIDIA:** rodar as N rodadas de um mesmo experimento **na mesma instância** (evita confundir variância de host com variância de execução); repetir um subconjunto em uma segunda instância para estimar a variância entre hosts
- [ ] Complementar com números publicados na literatura onde a execução pareada não cobrir (explicitar no texto quais comparações são pareadas e quais são indiretas)
- [ ] Coletar métricas em formato versionável (CSV/JSON) no repo: tempo, FPS, PSNR, SSIM, LPIPS, potência amostrada, energia integrada
- [ ] Documentar cada bug/regressão de correção encontrado como achado empírico do Cap. 5
- [ ] **(novo, decorre do reenquadramento)** Executar **primeiro** a coluna da 5070 Ti (`gsplat` CUDA × VkSplat Vulkan × Taichi→CUDA × Taichi→Vulkan, mesma instância) — é a afirmação principal e a única sob controle total. Só depois o lado AMD

> **Cortes candidatos — Sprint 3**
>
> | Item | Ação sugerida | Justificativa |
> |---|---|---|
> | Execução do PR #1297 (HIP) | **Cortar** | Consequência do corte no Sprint 0 |
> | Baseline PyTorch + ROCm como experimento | **Cortar** enquanto medição de desempenho | Permanece como evidência de H4, não como linha de tabela de performance |
> | Eixo cross-vendor completo | **Cortável sem perder o TCC** se a vast.ai não fechar | A afirmação principal é intra-máquina. Este eixo é "exploratório" na hierarquia de §2 |
> | Mip-NeRF 360 | **Cortar** se 15 GiB de RAM não segurarem as cenas grandes | Cenas como `bicycle`/`garden` são pesadas no carregamento e no COLMAP |
> | N ≥ 3 rodadas em todas as células | **Reduzir** N nas células exploratórias, manter N cheio nas células da afirmação principal | Concentra orçamento de tempo onde a evidência precisa ser forte |

### Sprint 4: Cap. 5 + Cap. 6 + revisão (semanas 9-10: 19/out → 01/nov/26)

- [ ] Escrever Cap. 5: Resultados e Discussão, estruturada nas 4 dimensões (performance, portabilidade, energia, gap funcional)
- [ ] **(novo)** Escrever Cap. 6: Conclusão (síntese, trabalhos futuros) — antecipado do Sprint 5, para redigir com os resultados frescos
- [ ] Revisar Cap. 2, Cap. 3 e Cap. 4 à luz dos resultados
- [ ] **(novo, decorre do reenquadramento)** Estruturar o Cap. 5 pela **hierarquia de afirmações** de §2 (principal → secundária → exploratória → bibliográfica), não pelas 4 dimensões de métrica. A dimensão é *como* se mede; a hierarquia é *o quanto se pode afirmar*
- [ ] **(novo)** Redigir explicitamente o veredito de cada hipótese contra seu critério de falsificação, incluindo as refutadas
- [ ] **(novo)** Se a estratégia escolhida no Sprint 2 foi manter `.md`, **migrar para `abntex2` aqui** — não no Sprint 5

> **Cortes candidatos — Sprint 4**
>
> | Item | Ação sugerida | Justificativa |
> |---|---|---|
> | Dimensão de energia (H3) | **Cortável** se a instrumentação não fechar; declarar a exclusão no Cap. 4 | Já previsto nas ressalvas diferidas de §8 |
> | Cap. 5 sobre as 4 dimensões | **Sustentável com 2 dos 4 eixos** (principal + bibliográfico) | Consequência direta da hierarquia de afirmações |

### Sprint 5: Fechamento (semana 11: 02/nov → 06/nov/26)

> **Cinco dias úteis, terminando no depósito.** Cap. 4 foi para o Sprint 2, Cap. 6 para o Sprint 4 e a migração LaTeX saiu daqui justamente para esta semana caber. Não acrescentar tarefa estrutural.
>
> **A preparação da defesa não entra aqui** — `06/nov` é depósito, a defesa vem depois. Slides, ensaio e respostas prováveis da banca são trabalho pós-janela.

- [ ] Escrever Cap. 1: Introdução (motivação, objetivo, contribuições)
- [ ] Escrever resumo + abstract (PT-BR e EN)
- [ ] Revisão integral
- [ ] Validar formatação ABNT no modelo `abntex2` (a migração em si já deve estar feita)
- [ ] Conferir os requisitos formais de depósito da UFC (ficha catalográfica, folha de aprovação, formato de arquivo, prazo e canal de entrega) — **verificar isso na semana 1, não agora no fim**
- [ ] **Depósito em 06/nov**
- [ ] **(novo, decorre do reenquadramento)** Em "trabalhos futuros" do Cap. 6, registrar os itens cortados como continuação natural: port de MLP fundido para WMMA/RDNA 4 (`tiny-rocm-nn`), rota HIP para 3DGS, e caracterização por roofline

> **Cortes candidatos — Sprint 5**
>
> | Item | Ação sugerida | Justificativa |
> |---|---|---|
> | Revisão integral | **Priorizar** Cap. 1, 5 e 6 (o que a banca lê primeiro e com mais atenção) | Em 5 dias não há tempo de revisar 6 capítulos com o mesmo cuidado |

### Pós-janela (após 06/nov, fora do cronograma de execução)

- [ ] Preparar a defesa: slides, ensaio, antecipar as perguntas da banca — incluindo a de "onde está a ciência", já endereçada pelo enquadramento de §2
- [ ] Aplicar correções pós-banca e entregar a versão final


## 6. Decisões registradas

| Data | Decisão | Justificativa |
|---|---|---|
| 2026-06-23 | Tipo de TCC: monografia bibliográfica com experimento próprio | Hardware disponível (RX 9070 XT) e gap empírico real no estado da prática |
| 2026-06-23 | Norma: ABNT | Padrão UFC |
| 2026-06-23 | Formato: `.md` agora, LaTeX `abntex2` no fim | Iteração rápida agora; conformidade ABNT no fim |
| 2026-06-23 | Setup de execução: Tailscale + SSH + git | Iteração ágil com debug remoto; pausado para retomar antes do Sprint 0 |
| 2026-06-23 | Caminho experimental: 3DGS via PR #1297 + VkSplat (Vulkan), Instant-NGP via taichi-ngp-renderer, baseline PyTorch+ROCm | Verificação de fontes primárias confirma viabilidade; tiny-cuda-nn AMD direto não é viável (CDNA-only) |
| 2026-06-23 | **Reformulação do escopo: TCC é análise comparativa CUDA × não-CUDA, não trabalho de portabilidade própria** | VkSplat e Linyou/taichi-ngp-renderer já fornecem implementações não-CUDA, então o foco move-se para medição e comparação nas 4 dimensões (performance, portabilidade, energia, gap funcional) |
| 2026-08-06 | Re-verificação de fontes primárias (após perda da memória `reference_experimento_rdna4.md` em reinstall) confirma viabilidade geral, mas rebaixa a confiança no VkSplat e no PR #1297 como baselines "prontos" | PR #1297 está parado há ~8 meses sem atividade; VkSplat ainda não foi testado pelos autores em RDNA 4 (só até RDNA 3) e o paper está "submitted", não aceito em Eurographics 2026 — ver `bibliografia/verificacao-experimento-rdna4.md` |
| 2026-08-06 | **Lado CUDA será executado em RTX 5070 Ti alugada na vast.ai** (resolve o bloqueante de hardware NVIDIA) | Custo baixo viabiliza execução pareada CUDA × não-CUDA nos mesmos datasets e protocolo, em vez de comparação indireta com números de papers; RTX 5070 Ti é a concorrente direta de mercado da RX 9070 XT (mesma geração, mesma faixa de preço/TDP), o que fortalece a comparabilidade. Introduz ameaças de validade próprias do ambiente de nuvem — ver §8 |
| 2026-08-20 | **Reenquadramento científico: de benchmarking comparativo para decomposição do custo de abstração** (ver §2) | Crítica de "falta de produção de ciência" levantada por um segundo professor. Procede contra o desenho anterior: (a) três fatores variavam simultaneamente, tornando o resultado inatribuível; (b) as hipóteses afirmavam magnitude, que envelhece, em vez de mecanismo, que generaliza. Correção é de moldura, não de tema — nenhuma leitura ou verificação já feita é descartada |
| 2026-08-20 | **Desenho fatorial com a coluna intra-máquina como afirmação principal** | A comparação cross-vendor é inblindável (host de nuvem, código distinto, drivers distintos). A comparação intra-máquina — mesmo hardware, mesmo dataset, mesmo commit, só o backend varia — é totalmente controlável e é onde a evidência é forte. Hierarquizar em vez de tentar blindar tudo |
| 2026-08-20 | **Vulkan passa a caminho crítico; ROCm rebaixado a objeto de análise documental** | Vulkan é a única pilha já parcialmente pronta na máquina, não depende da restrição de SO do ROCm nem dos grupos `render`/`video`. H4 sustenta-se em evidência documental já coletada, sem exigir instalação bem-sucedida — uma instalação que falhe vira dado |
| 2026-08-20 | **Pré-registro do protocolo experimental em git antes do Sprint 3** | Custo próximo de zero; o histórico do repositório passa a provar que o protocolo não foi ajustado aos resultados. Endereça diretamente a crítica de rigor experimental |
| 2026-08-20 | **Novo título de trabalho:** "Renderização neural em hardware heterogêneo: decomposição do custo de desempenho de backends agnósticos de fornecedor". Formulação anterior preservada em §1 como **título alternativo** | Mantém o título principal já validado pelo orientador e altera só o subtítulo — sinaliza mecanismo (decomposição) em vez de medição comparativa, sem prometer magnitude nem se comprometer com um pipeline que ainda não subiu |

## 7. Decisões pendentes

- [x] ~~**BLOQUEANTE: acesso a hardware NVIDIA contemporâneo**~~ **RESOLVIDO em 2026-08-06:** RTX 5070 Ti alugada na vast.ai; disponibilidade no catálogo confirmada pelo aluno em 2026-08-06. Pendências derivadas (ver §8): (a) validar que `nvidia-smi --query-gpu=power.draw` funciona no container alugado; (b) definir critérios de seleção de instância (PCIe x16, CPU/RAM adequados) para não confundir H1; (c) decidir como tratar a métrica "tempo até bring-up" dada a imagem Docker pré-construída
- [x] ~~Hospedagem do repositório git: GitHub privado / GitLab UFC / só local~~ **RESOLVIDO** (constatado em 2026-08-20): GitHub, remote `origin` = `github-personal:fabio-gabriel/tcc.git`, branch `main` sincronizada. A decisão já havia sido tomada na prática sem ser registrada aqui
- [ ] **(2026-08-20) Decidir sobre o SO:** reinstalar/dual-boot Ubuntu 24.04 LTS (traz ROCm de volta como rota executável) ou permanecer no 26.04 (ROCm fica só como objeto documental de H4). Ver §8
- [ ] Datasets finais: Synthetic-NeRF + Mip-NeRF 360 + Tanks and Temples? Outro?
- [ ] Energia: confirmar instrumentação no Sprint 0. O `rocm-smi --showpower` reporta corretamente em RDNA 4? Caso contrário, plano B (medidor externo de tomada para potência total da workstation, ou outro método)
- [x] Validação bibliográfica do paper/repo VkSplat (arXiv:2605.00219) — confirmado real e ativo em 2026-08-06 (ver `bibliografia/verificacao-experimento-rdna4.md`); **pendente:** bring-up prático na RX 9070 XT, já que os autores só testaram até RDNA 3 (RX 7800 XT) e o paper ainda está "submitted" (não aceito) em Eurographics 2026

## 8. Riscos e ameaças à validade

> **Nota de leitura (2026-08-20):** as linhas anteriores a 2026-08-20 referem-se às hipóteses na numeração antiga. Após o reenquadramento de §2, "H1" designa a heterogeneidade do custo de abstração e "H2" a decomposição fatorial — onde o texto antigo diz "confunde H1" (comparação de desempenho cross-vendor), leia "confunde o eixo exploratório da hierarquia de afirmações".

| Risco | Impacto | Mitigação |
|---|---|---|
| ~~**Sem hardware NVIDIA**~~ **RESOLVIDO (2026-08-06):** lado CUDA em RTX 5070 Ti alugada na vast.ai | — | Execução pareada agora é possível; riscos residuais nas 4 linhas seguintes |
| **Energia (H3) em ambiente de nuvem não-controlado:** o lado AMD roda na sua bancada (temperatura, gabinete, refrigeração conhecidos), o lado NVIDIA num host desconhecido | Comparação de energia system-level fica indefensável; até a potência de placa sofre efeito indireto de temperatura ambiente sobre clocks/ventoinha | Restringir H3 explicitamente a **potência de placa** (telemetria interna da GPU via `nvidia-smi`/`rocm-smi`), nunca energia do sistema; registrar temperatura da GPU junto da potência; declarar a limitação no Cap. 4 |
| **Variância de host da vast.ai confunde H1:** instâncias variam em CPU, RAM, lanes PCIe (rigs de mineração com riser x1/x4 são comuns) e disco — e treino de NeRF/3DGS tem componente real de CPU/IO | Um host fraco faz o lado NVIDIA parecer artificialmente lento, invalidando a comparação de performance | Filtrar instâncias por PCIe x16 + CPU/RAM adequados; registrar especificações do host de cada sessão; rodar as N repetições na mesma instância; repetir subconjunto em segundo host para medir variância entre hosts |
| **"Tempo até bring-up" deixa de ser comparável:** a vast.ai entrega imagem Docker com CUDA+PyTorch pré-construídos (setup ≈ 0 por construção), contra instalação ROCm do zero no Ubuntu | A dimensão de portabilidade favoreceria CUDA por artefato do provedor, não por mérito técnico | Escolher uma das opções e declarar: (a) medir bring-up a partir de imagem base limpa nos dois lados, (b) abandonar tempo-de-bring-up e manter tamanho de patch + contagem de bugs como proxies de portabilidade, ou (c) reportar com ressalva explícita |
| **Instância da vast.ai é efêmera:** desaparece ao ser liberada | Resultados não reproduzíveis se o ambiente não for capturado | Snapshot obrigatório por sessão: versão de driver, CUDA, digest da imagem Docker, CPU/RAM/PCIe do host, `nvidia-smi -q` completo |
| Bugs ativos em PyTorch+ROCm RDNA 4 | Resultados podem incluir falhas de correção, não só de desempenho | Documentar como achado empírico; reportar issue upstream se inédito |
| PR #1297 do 3DGS é rascunho da comunidade, **parado há ~8 meses sem atividade** (confirmado 2026-08-06) | Pode regressar, exigir patch local, ou já estar desatualizado contra o `main` upstream | Forkar e fixar commit; documentar versões usadas; testar cedo no Sprint 0 para não descobrir problemas tarde |
| VkSplat confirmado real (paper+repo existem e estão ativos), mas **não testado em RDNA 4 pelos autores** (só até RDNA 3) e paper ainda "submitted", não aceito em Eurographics 2026 | Baseline-chave do lado Vulkan pode não funcionar de primeira em RDNA 4; bring-up na 9070 XT passa a ser validação original, não replicação de resultado já demonstrado no mesmo hardware | Bring-up continua sendo a primeira tarefa prática do Sprint 0; não citar como "aceito" em Eurographics até confirmação |
| `rocm-smi --showpower` pode não reportar corretamente em RDNA 4 | H3 (energia) fica comprometida | Validar no Sprint 0; plano B com medidor externo de tomada |
| **Janela de 10 semanas e 5 dias** (24/ago → **depósito em 06/nov**, recalculada em 2026-08-20), sem nenhuma margem para atraso | Escopo estoura, ou o depósito atrasa | Cortes candidatos de §5 passam a escopo-base, não opções; Cap. 4 antecipado ao Sprint 2 e Cap. 6 ao Sprint 4 para desafogar o fim; preparação de defesa movida para pós-depósito; hard-cap de 1 semana no bring-up; go/no-go por pipeline no Sprint 0 |
| Mudanças de versão ROCm/PyTorch durante o experimento | Resultados não-reprodutíveis | Fixar versões com `requirements.txt` / Dockerfile; registrar SHA |
| Bibliografia "estava na cabeça" e ainda precisa ser fichada | Atraso no Cap. 2 | Fichamento em `bibliografia/fichamento.md` (~50 entradas). O aluno deve ler os papers prioritários listados ao final do fichamento |
| Comparativos cross-paper entre CUDA e ROCm são frágeis | Conclusões da H1 ficam fracas se não houver execução pareada | **Mitigado em 2026-08-06:** o aluguel da 5070 Ti na vast.ai permite execução pareada (mesmos datasets, protocolo e instrumentação nos dois lados). Onde ainda houver comparação indireta com literatura, marcar explicitamente como tal. **Mitigado estruturalmente em 2026-08-20:** a afirmação principal deixou de depender do eixo cross-vendor (ver hierarquia em §2) |
| **(2026-08-20) Ubuntu 26.04 está fora da matriz de suporte do ROCm**, que exige 24.04.4/22.04.5 ou RHEL 10.1/9.7. A máquina roda o LTS corrente, mais novo que o suportado | Rota ROCm/HIP não instala sem forçar codename ou reinstalar o SO. Kernel 7.0.0-29 e Mesa 26.0.3 também são mais novos que tudo que a bibliografia validou | Reenquadramento já removeu ROCm do caminho crítico. Decidir conscientemente (ver §7): dual-boot 24.04 traz a rota de volta; permanecer no 26.04 mantém ROCm como objeto documental de H4. **A própria situação é evidência de H4** — LTS corrente fora da matriz de suporte é exatamente "suporte declarado ≠ suporte efetivo" |
| **(2026-08-20) 15 GiB de RAM de sistema** na máquina de bancada | Cenas grandes de 3DGS (Mip-NeRF 360: `bicycle`, `garden`) e o pré-processamento COLMAP podem não caber | Synthetic-NeRF como dataset principal (leve, canônico). Mip-NeRF 360 entra só se couber, e como corte candidato declarado no Sprint 3 |
| **(2026-08-20) Python 3.14.4 é o único interpretador instalado**, sem 3.10–3.13 | Wheels de PyTorch-ROCm e Taichi não cobrem 3.14; nada instala como está | Instalar Python secundário na faixa suportada antes de qualquer bring-up. Custo baixo, mas precisa estar no caminho crítico do Sprint 0 |
| **(2026-08-20) rocWMMA (C.14) é o "trunfo central" do fichamento e não passou pela reconfirmação de 2026-08-06** | A afirmação mais forte do TCC repousa numa leitura de README de junho, com versão de referência defasada (ROCm 7.2.4 vs 7.14.0) | Reverificar antes de qualquer uso argumentativo. No enquadramento reformulado o peso dessa afirmação cai — ela sustenta H4, não a afirmação principal |

### Ressalvas diferidas para o momento da execução (registrado em 2026-08-06)

As duas ressalvas metodológicas abaixo são **decisões diferidas**, não pendências bloqueantes. Ficam registradas aqui para serem retomadas quando o experimento for de fato executado (Sprint 2 para o protocolo, Sprint 3 para a execução). Postura definida pelo aluno: **se não houver alternativa viável, a ressalva pode ser abandonada — declarando a limitação honestamente no texto — em vez de descartar a dimensão de medição.**

1. **Energia (H3) em host de nuvem não-controlado.** Plano atual: restringir a potência de placa e registrar temperatura. Se a instrumentação na vast.ai não permitir nem isso de forma confiável, a alternativa é reduzir H3 a uma análise qualitativa/bibliográfica, ou removê-la das hipóteses testadas — decidir com o Prof. Gilvan, não silenciosamente.
2. **Métrica "tempo até bring-up" viciada pela imagem Docker pré-construída.** Três saídas registradas na tabela acima. Se nenhuma for praticável, a métrica sai da dimensão de portabilidade e o peso migra para tamanho de patch + contagem de bugs upstream, com a exclusão justificada no Cap. 4.



## 9. Estado atual (atualizado em 2026-08-20)

**Progresso contra o cronograma**

- A janela de execução foi **recalculada em 2026-08-20** para 24/ago → 06/nov/2026 (**10 semanas e 5 dias**), substituindo o cronograma original de 17 semanas que tinha início em 23/jun e término estimado em 23/nov. O plano original acumulou atraso; esta janela é a reprogramação, e o aluno está trabalhando para compensar
- **`06/nov` é a data de depósito**, não de defesa (confirmado pelo aluno em 2026-08-20). A defesa e eventuais correções são posteriores e ficam fora da janela
- **Nenhum sprint concluído.** O Sprint 0 está parcial: os itens de git e o inventário de ambiente estão feitos, o bring-up não começou
- **Zero papers lidos** das 54 entradas do fichamento; **zero capítulos escritos**; **zero execuções** de pipeline
- Efeito prático da compressão: os cortes candidatos anotados em §5 devem ser tratados como escopo-base. Ver §4, "Consequências da compressão"

**Repositório**

- Git **inicializado** (primeiro commit em 2026-06-23), branch `main`, **4 commits**: `78b7fbc` initial commit → `ab4fdd0` state of the art study → `acadd3c` Sprint 0: script de inventário + verificação de viabilidade → `004f23d` inventario
- **Hospedado no GitHub** — remote `origin` = `github-personal:fabio-gabriel/tcc.git` (alias SSH), sincronizado com o local. Isso resolve na prática a pendência de hospedagem de §7 e os dois itens de git do Sprint 0
- `.gitignore` presente

**Material produzido**

- `PLANO.md` (este arquivo) e `CLAUDE.md`
- `bibliografia/fichamento.md`: **54 entradas em 5 eixos (A–E)**. Nenhuma marcada como lida — o campo `status_validacao` rastreia verificação de *metadados*, não leitura. O **Eixo E inteiro está `incerto`** (criado em 2026-08-20, metadados não validados)
- `bibliografia/verificacao-experimento-rdna4.md`: verificação de viabilidade concluída em 2026-06-23 e reconfirmada em fontes primárias em 2026-08-06
- `experimentos/00-inventario/`: script `inventario-ambiente.sh` + saída `inventario-fabio-computer-20260818T212900Z.md` (2026-08-18)
- Material de partida: 3 PDFs exploratórios na raiz (números a tratar com cautela)
- **Não há** capítulos da monografia escritos, nem código de experimento

**Ambiente de execução (inventário de 2026-08-18) — nenhum pipeline rodou ainda**

- GPU detectada em PCI (`Navi 48 [1002:7550]`) com `amdgpu` in-kernel ativo e `/dev/kfd` criado — mas o inventário **não desambigua** se a placa é a XT (a string do `pci.ids` cobre 9070 / 9070 XT / 9070 GRE)
- **Nada instalado:** sem ROCm, PyTorch, Taichi, pip, gcc/clang, cmake, hipcc, glslc, COLMAP, docker
- Ubuntu 26.04 (fora da matriz ROCm), kernel 7.0.0-29, Python 3.14.4 como único interpretador, 15 GiB de RAM, 124 GB livres
- Usuário fora dos grupos `render`/`video` (embora os nós de dispositivo exibam ACL POSIX, o que pode conceder acesso por outra via — não testado)
- Vulkan parcialmente pronto: RADV + `libvulkan1` instalados, faltando `vulkan-tools` e compiladores de shader
- **6 de 6 gates reprovados** pelo próprio script — com uma ressalva: o gate de potência (H3) é atendível via `sysfs`/hwmon, que funcionou; a tabela só avaliou a via `rocm-smi` (ver §3)
- Nenhum indício de execução prévia: sem datasets, sem checkpoints, `$HOME` com 420 MB

**Outros**

- Domínios liberados no sandbox: `www.google.com`, `rocm.docs.amd.com`, `github.com`, `api.github.com`, `www.amd.com`, `arxiv.org`, `pytorch.org`, `docs.taichi-lang.org`, `raw.githubusercontent.com`, `phoronix.com`, `pypi.org`
- Tailscale: pausado a pedido do usuário; retomar antes do bring-up

## 10. Materiais e localização

- `CLAUDE.md`: papel do assistente, convenções, escopo confirmado, resumo do enquadramento científico
- `PLANO.md`: este arquivo — **fonte de verdade do enquadramento científico (§2)**, cronograma, sprints e decisões
- `bibliografia/fichamento.md`: fichamento do estado da arte, 54 entradas em 5 eixos (em construção)
- `bibliografia/verificacao-experimento-rdna4.md`: log de verificação de viabilidade do experimento (fonte de verdade sobre suporte ROCm, status de PRs/repos de terceiros e bugs upstream, versionado)
- `experimentos/00-inventario/`: script de inventário de ambiente e suas saídas datadas
- 3 PDFs iniciais na raiz (material exploratório, não usar como fonte direta sem validar)

**Memórias persistentes — atenção, estão órfãs (verificado em 2026-08-20)**

Existem 3 arquivos de memória em `~/.claude/projects/-Users-fabiogomes-code-tcc/memory/`: `MEMORY.md`, `postura_ressalvas_metodologicas.md` e `reference_experimento_rdna4.md`. Todos são **ponteiros curtos**, não fatos brutos — os fatos vivem no repositório, por decisão registrada após a perda de uma memória anterior em reinstall.

Porém, o slug daquele diretório corresponde ao caminho **antigo** do projeto (`/Users/fabiogomes/code/tcc`). O projeto vive hoje em `/Users/fabiogomes/code/etc/tcc`, cujo diretório de memória correspondente está **vazio**. Consequência prática: **essas 3 memórias não são mais carregadas automaticamente.** Duas saídas: recriá-las no caminho atual, ou ignorá-las — o conteúdo delas já está refletido neste `PLANO.md` (a postura sobre ressalvas está em §8, e o ponteiro para os fatos de viabilidade está logo acima).
