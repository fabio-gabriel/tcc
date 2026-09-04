# PLANO — Reprodutibilidade em treino de 3D Gaussian Splatting

> **Fonte de verdade do enquadramento científico (§2).** Em divergência com o `CLAUDE.md`, este arquivo prevalece.
>
> Criado em 2026-08-26, após três reenquadramentos sucessivos (2026-08-20, 2026-08-25, 2026-08-26) registrados em §6. **Ainda não validado com o orientador institucional.**

## 1. Identidade

| Campo | Valor |
|---|---|
| Curso / instituição | Engenharia de Computação, Universidade Federal do Ceará (UFC) |
| Orientador institucional | Prof. Gilvan |
| Depósito | **06/nov/2026** (data institucional; defesa e correções são posteriores) |
| Janela útil | 2026-08-26 → 2026-11-06 — **10 semanas e 2 dias** |
| Norma | ABNT: NBR 6023, NBR 10520, NBR 14724 |
| Formato | Markdown, com migração futura para `abntex2` |
| Tipo | Monografia com experimento próprio e intervenção de código de escopo limitado |

**Título de trabalho:**

> Reprodutibilidade em treino de 3D Gaussian Splatting: dispersão entre execuções, acumulação atômica não-associativa e a comparabilidade de resultados publicados

**Títulos anteriores, mantidos como registro:**

1. *Renderização Neural em Hardware Heterogêneo — Portabilidade e desempenho de NeRF/3DGS em GPUs AMD RDNA 4* (até 2026-08-20)
2. *Renderização neural em hardware heterogêneo: decomposição do custo de desempenho de backends agnósticos de fornecedor* (2026-08-20 a 2026-08-26)
3. *Um MLP fundido para campos neurais em backend agnóstico de fornecedor* (formulação de 2026-08-26, abandonada no mesmo dia — ver §6)

## 2. Enquadramento científico

### 2.1 Pergunta

> **Quão reprodutíveis são as métricas de qualidade no treino de 3D Gaussian Splatting, e o que a dispersão entre execuções idênticas implica para a comparabilidade dos resultados publicados na área?**

Sub-perguntas:

1. Qual é a dispersão de PSNR, SSIM e LPIPS entre N execuções **idênticas** — mesma cena, mesma seed, mesmo commit, mesma máquina, mesma configuração?
2. Essa dispersão se manifesta apenas nas métricas de imagem, ou também nos **parâmetros do modelo** (número de gaussianas, posições, escalas, opacidades)?
3. A dispersão intra-configuração é maior ou igual ao menor delta de PSNR que a área apresenta como contribuição?
4. Quais são as fontes de não-determinismo, e qual delas domina? Eliminar a dominante elimina a dispersão, e a que custo?
5. Os valores de qualidade publicados pelos autores do VkSplat se reproduzem em hardware que eles não testaram (RDNA 4)?

### 2.1.1 Correção de premissa — 2026-08-26, ler antes de escrever qualquer texto

A formulação inicial deste plano supunha que **a área não reporta dispersão** entre execuções, e que isso tornaria as comparações publicadas incomparáveis. **A premissa é falsa e foi falsificada em levantamento no mesmo dia.** De 5 trabalhos cujo corpo de texto foi examinado, **3 reportam dispersão**:

| Trabalho | Execuções | Dispersão | Seed |
|---|---|---|---|
| **3DGS-MCMC** (NeurIPS 2024) | 3 | σ (Apêndice B, Tab. 5) | *"for a given seed"* — seed por execução |
| **VkSplat** (EG 2026) | **5** | **IC 90%** | não declarado no artigo |
| **FreeTimeGS++** (arXiv:2605.03337) | **10** | média ± σ, com figura de distribuição | `seed = S + r` — **variam deliberadamente** |
| Mip-Splatting (CVPR 2024) | 1 | não | não menciona |
| gsplat (JMLR 2025) | 1 | não | não menciona |

O FreeTimeGS++ tem uma subseção inteira intitulada **"Secret 5: Single-run scores can hide run-to-run variation"**, com 10 execuções por cena, distribuição plotada, e **uma intervenção que reduz a variância** com custo/benefício medido — estruturalmente análoga ao eixo 2 deste trabalho. E o **NerfBaselines** (NeurIPS 2025 Datasets & Benchmarks, arXiv:2406.17345) já publicou a conclusão metodológica de que *"even tiny differences in the evaluation protocols ... can artificially boost the performance"*, levantando *"questions about the validity of quantitative comparisons performed in the literature"* — por causa de **protocolo de avaliação**, não de estocasticidade de treino.

**Escrever "a área não reporta dispersão" seria erro factual verificável em dez minutos por qualquer membro de banca.** Está proibido.

### 2.1.3 O que se pode e o que não se pode alegar — 2026-08-26

Varredura de issues e PRs em `graphdeco-inria/gaussian-splatting`, `graphdeco-inria/diff-gaussian-rasterization`, `nerfstudio-project/gsplat`, `nerfstudio-project/nerfstudio` e `harry7557558/vksplat`.

**Não se pode alegar descoberta nem identificação do fenômeno.** Ele é reconhecido pelos próprios autores e mantenedores:

- **Kerbl** (coautor do 3DGS), em `gaussian-splatting` #89, 2023-08-14: *"due to the way that the differentiable rasterizer is implemented, there will always be SOME randomness caused by GPU scheduling"*, e *"The GPU scheduling will cause random behavior, which was not a problem for us, this could only be avoided with a rigorous rewrite."* A issue foi **fechada sem correção**; usuários voltaram a relatar o problema em 2023-11, 2024-07, 2024-11 e 2025-07.
- **`maturk`** (mantenedor de nerfstudio/gsplat), em `nerfstudio` #2996, 2024-03-11, dá a explicação mecanística completa: *"Many of the operations, most importantly the gradient passes, use CUDA atomics to accumulate gradients. These are inherently nondeterministic... For some types of atomic operations, the final result is unaffected by the order in which they are executed (for example, integer addition). However, floating-point addition which is in the gradient passes does not produce the same result when executed in a different order."*

Se a monografia disser "este trabalho identifica que…", a banca acha a issue #89 em dois minutos.

**O que a evidência sustenta, e é bastante:**

1. **A lacuna de quantificação é real.** Três anos e meio após #89, com o fenômeno reconhecido por autores e mantenedores, o único dado numérico público é uma amplitude de 45 execuções num relato de usuário **com hiperparâmetros alterados** (`percent_dense=1e-5`) e sem N por configuração, média, desvio ou IC. Medir com N adequado, distribuição e IC é contribuição legítima.
2. **Não existe modo determinístico.** Zero issues, PRs, flags ou branches propondo treino determinístico nos cinco repositórios — incluindo o `vksplat`, que tem **0 issues e 0 PRs** apesar de ser um backend Vulkan de treino 3DGS. Resultado negativo verificado.
3. **A atribuição por ablação continua original.** Ninguém separou as fontes nem mediu o resíduo atribuível às atômicas.

**Redação obrigatória:** deslocar a alegação de *descoberta* para *quantificação e atribuição*. O fenômeno é reconhecido desde 2023 e atribuído a atômicas de ponto flutuante em 2024, **mas permanece não quantificado**. Citar o reconhecimento em vez de escondê-lo é o que torna o trabalho robusto a arguição.

> **Pendência de forma ABNT:** comentários em issue de repositório público são fonte primária legítima, mas exigem decisão de formato de citação (autor, data, plataforma, URL, data de acesso). Resolver antes do Cap. 2.

### 2.1.4 Achado de terceiro que deve ser central, não nota de rodapé

`nerfstudio-project/gsplat` **PR #970**, aberto em 2026-06-02 por **`jeffdaily`, engenheiro da AMD**, portando gsplat para ROCm/HIP. Citação literal do corpo do PR:

> *"Matching CUDA's one-atomic-per-label granularity (not a per-lane fan-out) is load-bearing: the larger atomic count changes float accumulation order and pushed the `v_viewmats` gradient past gsplat's own test tolerance."*

E sobre otimização numérica:

> *"ROCm `-ffast-math` is more aggressive than CUDA's and perturbed ill-conditioned projection-covariance gradients past tolerance, so `FAST_MATH` defaults off on ROCm."*

É evidência primária, de engenheiro do fornecedor, de que **trocar o backend altera a ordem de acumulação atômica o suficiente para violar as tolerâncias de teste do próprio projeto** — não por bug, mas por diferença estrutural do modelo de execução. Sustenta o mecanismo deste TCC com força que nenhuma referência acadêmica encontrada oferece.

### 2.1.5 A reformulação que sobrevive

> A dispersão entre execuções de 3DGS é reconhecida e ocasionalmente reportada, mas **sempre com a seed variando** — o que confunde **estocasticidade algorítmica** com **não-determinismo de execução**. Nenhum trabalho localizado isola o não-determinismo **a seed fixa**; nenhum atribui a causa a um mecanismo numérico específico; nenhum mede o custo de eliminá-lo.

Consequências:

- O **eixo 2 (intervenção) passa a ser a contribuição principal**, não complemento.
- O Cap. 1 deve declarar a diferença em relação ao FreeTimeGS++ em quatro dimensões explícitas: objeto (3DGS estático × 4DGS dinâmico), fonte de variação (seed fixa × seed variável), causa atribuída (mecanismo numérico × *"small stochastic differences"* não investigadas), e natureza da intervenção (numérica × fotométrica).
- O posicionamento em relação ao NerfBaselines é: *eles mostraram que o protocolo compromete a comparabilidade; este trabalho mostra que, mesmo com protocolo idêntico, a execução também compromete.*
- **FreeTimeGS++ e NerfBaselines precisam ser lidos integralmente antes do Cap. 2.** São os dois trabalhos que mais podem erodir a originalidade, e nenhum dos dois foi lido — do primeiro só o HTML principal, do segundo só o resumo.

### 2.2 Mecanismo

O backward do 3D Gaussian Splatting acumula gradientes de parâmetros por meio de **adição atômica em ponto flutuante** — no VkSplat, via a extensão `VK_EXT_shader_atomic_float`, requerida incondicionalmente na criação do dispositivo. Duas propriedades se combinam:

1. A adição em ponto flutuante **não é associativa**: `(a+b)+c ≠ a+(b+c)` em geral.
2. A **ordem** em que invocações concorrentes de GPU executam suas adições atômicas não é determinística nem especificada.

Portanto, o gradiente acumulado difere entre execuções, a trajetória de otimização diverge, e o modelo final não é o mesmo. Isto **não é bug**: é consequência esperada do modelo de execução. O que não se sabe é a **magnitude** do efeito nas métricas reportadas, nem se ela é grande o bastante para comprometer comparações publicadas.

### 2.3 Hipóteses, com critério de falsificação declarado

**H1 — Existe não-determinismo detectável.**
Execuções idênticas de treino de 3DGS produzem modelos distintos e métricas de qualidade distintas.
*Refutada se:* N execuções produzirem parâmetros bit-idênticos, **ou** se a dispersão de PSNR ficar abaixo do limiar de precisão de medição pré-registrado.

**H2 — A dispersão é metodologicamente relevante.**
A dispersão intra-configuração de PSNR é **maior ou igual ao menor delta de PSNR apresentado como contribuição** no conjunto de trabalhos levantados.
*Refutada se:* a dispersão for menor que esse limiar.
*Limiar, fixado a partir de levantamento de 2026-08-26 (ver `bibliografia/fichamento.md` §Eixo A e a tabela de deltas):* **0,10 dB**. No regime canônico do Mip-NeRF 360, trabalhos de sistemas e eficiência reportam ganhos de **0,03 a 0,20 dB** — gsplat declara paridade com +0,05 dB e apresenta features de +0,03, +0,11 e +0,18 dB; Mip-Splatting reporta +0,09 dB contra o próprio 3DGS retreinado. Reformulações algorítmicas reais ficam em outra faixa (3DGS-MCMC: +0,59 dB), e ganhos ≥1 dB vêm de mudar o regime, degradar o baseline ou trocar de dataset.
*Calibração disponível:* 3DGS-MCMC publicou σ de PSNR sobre 3 execuções **com seed variável** no Mip-NeRF 360 — **0,0276 dB** (init SfM) e **0,0524 dB** (init aleatória), em nível de dataset. A dispersão a seed **fixa** medida por este trabalho deve ser **menor** que esses valores; se não for, isso é achado.

**H3a — A acumulação atômica em ponto flutuante é a fonte residual do não-determinismo.**
Após eliminadas as demais fontes identificadas (ordem de visitação de imagens e seleção de kernel por latência), a dispersão remanescente entre execuções idênticas é atribuível à acumulação atômica em `float32` no backward de rasterização. Substituí-la por acumulação associativa (atômicos inteiros em ponto fixo) leva a dispersão a zero.
*Refutada se:* a dispersão persistir após a intervenção — o que indicaria fonte adicional não identificada (candidato conhecido: reordenação Morton, ver §7) e passaria a ser o achado.

**H3b — Repetibilidade não implica estabilidade.**
Ainda que a intervenção torne as execuções repetíveis, o treino permanece **instável**: uma perturbação mínima e controlada na condição inicial produz divergência da mesma ordem de magnitude que a dispersão medida em H1.
*Refutada se:* a perturbação mínima produzir divergência substancialmente menor que a dispersão de H1.
*Teste:* injetar alteração de **um bit** em um parâmetro inicial e repetir o treino.

> **Por que H3b existe.** Summers e Dinneen (2021, arXiv:2103.04514) reportam que *"even one-bit changes in initial parameters result in models converging to vastly different values"*. Se o treino é intrinsecamente instável, tornar o atômico determinístico deixa o resultado *repetível* sem torná-lo *robusto*. A distinção entre **reprodutibilidade** e **estabilidade** precisa estar explícita no texto; H3b é o teste que a separa.

### 2.3.1 Escada de ablação — o desenho que substitui a hipótese única

A auditoria do código do VkSplat em 2026-08-26 (commit `b3ad2b0`) identificou **três** fontes de não-determinismo, não uma. Isso permite trocar uma hipótese monolítica por uma **escada de ablação**, em que cada degrau é uma intervenção controlada com desfecho previsto — desenho consideravelmente mais forte.

| Degrau | Intervenção | Fonte eliminada | Dispersão prevista |
|---|---|---|---|
| **D0** | nenhuma (baseline *as-is*) | — | máxima; soma de todas as fontes |
| **D1** | semear `random.shuffle` (`simple_trainer.py:203-208`, onde `random.seed(step)` está **comentado**) | ordem de visitação das imagens de treino | menor que D0 |
| **D2** | `RASTERIZE_BACKWARD_USE_SCHEDULING 0` (`src/config.h:24`) + recompilar | seleção de kernel por latência medida | menor que D1 |
| **D3** | acumulação em ponto fixo com atômicos inteiros nos 9 sítios de `_ATOMIC_ADD` | acumulação `float32` não-associativa | **zero**, se H3a se sustentar |

Cada degrau é uma medição de N execuções. O resíduo em D2 é a **contribuição isolada das atômicas** — e é a quantidade que nenhum trabalho localizado mediu.

**Consequência importante para a originalidade:** o VkSplat reporta 5 execuções com IC de 90%, mas a auditoria mostra que essas execuções **não podem ter sido repetições a seed fixa** — o lado GPU é sempre semeado com `42` (`gs_trainer.cpp:127`), enquanto o embaralhamento em Python não é semeado. Logo o IC publicado por eles mistura estocasticidade de ordem de dados com não-determinismo de execução. O eixo 1 deste trabalho **não é replicação** do que eles fizeram.

**H4 — exploratória, força de evidência menor.**
Os valores de PSNR/SSIM/LPIPS publicados pelos autores do VkSplat se reproduzem em RDNA 4 dentro da faixa de dispersão medida em H1.
*Refutada se:* os valores obtidos caírem fora dessa faixa.

### 2.4 Níveis de evidência

Substitui a "hierarquia de afirmações" dos planos anteriores. A propriedade desejada é a mesma: **se um nível superior desabar, o TCC continua de pé.**

| Nível | Conteúdo | Depende de |
|---|---|---|
| **N0** | VkSplat compila e treina uma cena em RDNA 4 | bring-up |
| **N1** | N ≥ 5 execuções idênticas concluem com métricas e modelos coletados | N0 |
| **N2** | Dispersão quantificada, com desvio-padrão e intervalo de confiança, em métricas **e** em parâmetros do modelo | N1 |
| **N3** | Intervenção determinística implementada, com efeito sobre a dispersão e custo medidos | N2 + código autoral |
| **N4** | Comparação com valores publicados pelos autores | N2 |

**N0 já é resultado publicável** — os autores do VkSplat testaram até RDNA 3 (RX 7800 XT); RDNA 4 não consta da lista "Tested with". Um bring-up que falhe, documentado, é contribuição.

O eixo **documental** — as observações categóricas sobre a superfície de API em `bibliografia/verificacao-vulkan-rdna4.md` — não aparece nesta escala porque **não depende de nenhum nível**. Já está coletado.

### 2.5 O que este trabalho não afirma

- Não afirma nada sobre desempenho comparado entre fornecedores, plataformas ou implementações de terceiros.
- Não compara com gsplat nem com CUDA: não há hardware NVIDIA. Onde houver referência a valores de terceiros, é **contra números publicados**, declarado como tal.
- Não afirma que o não-determinismo é defeito do VkSplat, do RADV ou da AMD. O mecanismo é geral a implementações de 3DGS que usem atômicos de ponto flutuante, o que inclui a implementação original em CUDA.
- **Não afirma originalidade algorítmica.** O problema de somatório reprodutível em redução paralela já foi resolvido em forma mais geral — Demmel e Nguyen (2013, 2015), Ahrens et al. (2020) e, no caso específico de redução em GPU com acumulador longo, Collange et al. (2015). A acumulação em ponto fixo aqui proposta é uma **variante simplificada e barata** dessas técnicas. A contribuição é **aplicá-la ao backward do 3DGS e quantificar o custo nesse contexto**, não inventar o método. Enquadrar assim desde a introdução, para não expor o trabalho a uma objeção de novidade que ele não precisa enfrentar.
- **Não afirma, por ora, que o tema é inédito.** A busca de originalidade está incompleta (ver `bibliografia/fichamento.md`, lacuna 2). Nenhum texto pode alegar novidade antes de concluída.

## 3. Caminho experimental

### 3.1 Pré-registro do protocolo — **obrigatório, em commit, antes da primeira execução medida**

Item mais importante desta seção. O protocolo deve fixar, **antes de ver qualquer dado**:

- Cena, dataset e resolução: **Mip-NeRF 360, `garden`, `images_4`**
- Commit exato do VkSplat (fork próprio, commit fixado)
- Número de iterações de treino e critério de parada
- Seed e o que mais é fixado (ordem de imagens, `eval_interval`)
- **N** — número de repetições
- Limiar de precisão de medição, abaixo do qual H1 é considerada refutada
- Limiar de relevância para H2, derivado de levantamento de diferenças publicadas feito antes
- Configuração de dispositivo: `deviceName` fixado, wave size fixado e declarado, `image_cache_device`
- Variáveis de ambiente relevantes (incluindo ausência de `RADV_DEBUG=llvm`)
- Estatística a usar e como a dispersão será reportada

O histórico do git passa a provar que o critério não foi ajustado aos resultados. **Sem isso, os eixos 1 e 2 são indefensáveis** — e a tentação de mexer no limiar depois de ver a dispersão é direta, porque o aluno tem interesse no resultado.

### 3.2 Instrumentação

O VkSplat já emite nativamente, sem alteração de código:

- `train.json`: `time_elapsed`, `breakdown` (tempo por estágio, via *timestamp query pools* do Vulkan), `vram`, `peak_vram`, `vram_breakdown`, `num_splats`
- `eval.json`: `psnr`, `ssim`, `lpips_vgg`, `lpips_alex` (via `torchmetrics`, executando em CPU na ausência de CUDA)
- `config.json`: configuração completa
- `splat.ply`: nuvem de gaussianas treinada

Código autoral necessário no eixo 1 — é instrumentação e análise, não pipeline:

1. **Harness de execução** que fixa dispositivo, seed e ambiente; captura o inventário por execução; e falha alto se o dispositivo selecionado não for a GPU esperada.
2. **Comparador de modelos** que lê dois `.ply` e quantifica divergência entre execuções: contagem de gaussianas, e distribuição de diferença em posição, escala, opacidade e coeficientes SH. **Comparar os parâmetros, não só o PSNR** — é o que distingue este trabalho de uma observação superficial, porque duas execuções podem convergir para PSNR semelhante por caminhos muito diferentes.
3. **Análise estatística** com dispersão, IC e visualização da distribuição.

### 3.3 A intervenção (eixo 2)

Substituir, em **um** estágio do backward, a adição atômica em ponto flutuante por acumulação em **ponto fixo com atômicos inteiros** — que são associativos, logo o resultado passa a ser independente da ordem.

Escopo deliberadamente estreito: um estágio, não o pipeline. Entregas: (a) a dispersão cai ou não; (b) o custo em tempo daquele estágio, medido pelo `breakdown` que já existe; (c) o erro introduzido pela quantização em ponto fixo, que é o preço numérico do determinismo.

**Escolhas a documentar:** número de bits fracionários, faixa dinâmica assumida para os gradientes, e o que acontece em saturação. São decisões de projeto de engenharia, e são o conteúdo técnico do capítulo.

**Risco declarado:** se o gradiente tiver faixa dinâmica larga demais, o ponto fixo degrada a qualidade — e aí o achado é o *trade-off* entre determinismo e qualidade, que também é resultado.

### 3.4 Métricas

| Grupo | O que |
|---|---|
| Qualidade | PSNR, SSIM, LPIPS (vgg e alex) — **sempre com dispersão sobre N execuções, nunca média nua** |
| Divergência de modelo | nº de gaussianas; distribuição de diferença de posição, escala, opacidade, SH entre execuções |
| Custo da intervenção | tempo do estágio modificado, do `breakdown`; VRAM |
| Erro da intervenção | diferença entre gradiente em ponto fixo e em FP32, em execução controlada |
| Ambiente | `deviceName`, wave size, versões, commit, variáveis de ambiente — por execução |
| Contaminação do escalonador | contagens de `_RasterizeBackwardScheduling_PerSplat` e `_Tensor_0_8_8` — por execução |

### 3.5 Plano estatístico

Ancorado em Hoefler e Belli (2015), lido em 2026-09-01 (ver `bibliografia/fichamento.md` E.1, com a ressalva sobre a versão da cópia de autor). O que é recomendação do artigo está assinalado; o resto é decisão deste trabalho.

**Nada de estatística paramétrica por padrão — e isto derruba a justificativa anterior para N=30.** O artigo é literal:

> *"Our experiments (Figure 2) and other authors show that the 30-40 samples as indicated in some textbooks are not sufficient."*

N na faixa de 30–40 **não** autoriza invocar o Teorema Central do Limite. N=30 continua viável; usá-lo *como argumento de normalidade* não. Some-se: distribuições normais *"are only rarely observed when measuring computer performance"*.

| Item | Decisão |
|---|---|
| Tendência central | **Mediana**, não média |
| Dispersão | Q1, Q3, mínimo, máximo, e **amplitude total (max − min)** |
| Intervalo de confiança | **CI 95% não-paramétrico da mediana** pelo rank de Le Boudec, citado pelo artigo: do rank ⌊(n − z(α/2)√n)/2⌋ ao rank ⌈(n + z(α/2)√n)/2⌉ + 1 |
| Normalidade | **Shapiro-Wilk + Q-Q plot** em apêndice — para documentar que a suposição foi checada, não assumida |
| Outliers | **Não remover** (recomendação literal). Se inevitável, Tukey 1,5×IQR **e reportar quantos foram removidos por experimento** |
| Comparação entre degraus | CIs não sobrepostos; **Kruskal-Wallis** para medianas não-normais; **tamanho de efeito** para efeitos pequenos |
| Agregação entre cenas | **não agregar** (ver abaixo) |
| Gráfico | Box + violin combinados, semântica dos *whiskers* declarada. **Não ligar D0–D3 por linha** — são níveis categóricos |

**Assimetria lógica a respeitar, citada:** *"If 1−α confidence intervals do not overlap, then one can be 1−α confident that there is a statistically significant difference. The converse is not true."* Sobreposição de CIs não prova ausência de efeito.

**Por que não agregar PSNR entre cenas.** PSNR é em dB, logo escala logarítmica; média aritmética de dB equivale a média geométrica do MSE. As Rules 3 e 4 do artigo (média aritmética só para custos, nunca fazer média de razões) não cobrem métricas de qualidade adimensionais, que ele não classifica. **A saída é não precisar da agregação:** a pergunta é sobre dispersão *dentro* de uma configuração, então reportar por par (cena × configuração) contorna o problema em vez de exigir defesa dele.

**Amplitude total é a métrica-manchete, não o CI.** O CI da mediana mede confiança *no experimento*; amplitude e quartis medem a **dispersão do fenômeno**, que é o objeto. O artigo trata dispersão como incômodo a reportar; aqui ela é o achado.

**Rule 11 reinterpretada.** O artigo recomenda mostrar limites superiores para dar interpretabilidade. Traduzido: o **degrau D3**, se produzir execuções repetíveis, é o **teto determinístico** contra o qual a dispersão dos degraus anteriores deve ser lida.

#### 3.5.1 Dimensionamento de N — critério sequencial, e a tensão com o pré-registro

O artigo não dá N fixo; dá critério de parada:

> *"we recommend recomputing the 1−α CI after each nᵢ = i·k, i ∈ ℕ measurements and stop the measurement once the required interval is reached. We recommend choosing k based on the cost of the experiment, e.g., k = 1 for expensive runs. Furthermore, we note that n > 5 measurements are needed to assess confidence intervals nonparametrically."*

Com ~15 min por execução, o regime não é o de *hero run* que motiva `k = 1`; **`k = 10`** é adequado.

Largura do CI da mediana pela fórmula de Le Boudec, α = 0,05, z = 1,96 (cálculo deste trabalho com a fórmula literal do artigo):

| N | Ranks do CI da mediana | Banda em percentil |
|---|---|---|
| 30 | 9 a 22 | ~30% – 73% |
| **50** | **18 a 33** | **~36% – 66%** |

**Decisão: `N_max = 50` por degrau**, avaliando o CI a cada 10 execuções, com parada antecipada se a largura-alvo for atingida. Custo: 4 × 50 × ~15 min ≈ **50 h de máquina**. Se estabilizar em N=20, documentar e parar; se não estabilizar em 50, **documentar também — é resultado**.

> **Tensão metodológica a declarar, que o artigo não aborda.** Parada sequencial adaptativa é decisão dependente dos dados. É aceitável **porque o critério é declarado a priori** — e é exatamente isso que o pré-registro prova. Logo o pré-registro deve fixar, antes de qualquer execução medida: **α, a largura-alvo `e`, o passo `k` e `N_max`**. Ajustar qualquer um depois de ver os dados invalida o eixo 1.

**Frase-modelo de reporte**, adaptável do artigo: *"We collected measurements until the 99% confidence interval was within 5% of our reported means."*

**O que não pode ser ancorado neste artigo:** *bootstrap*. Ele o exclui — *"More advanced statistical techniques such as bootstrap are beyond the scope of our work."* Se usado, justificar por Davison e Hinkley ou Efron e Tibshirani.

#### 3.5.2 Dado do artigo que serve à introdução

Levantamento dos autores sobre **95 artigos de HPC: apenas 15 mencionam alguma medida de variância, e apenas 2 reportam intervalo de confiança em torno da média.** E: *"51 out of 95 applicable papers use summarizing to present results. Only four of these specify the exact averaging method."*

É quantificação publicada da lacuna de prática — em HPC, não em renderização neural, e isso precisa ser dito. Mas generaliza o argumento e é muito mais forte que afirmação retórica. Combina com a contagem própria de 2026-08-26 sobre 3DGS (3 de 5 reportam dispersão, todos com seed variando).

#### 3.5.3 Conceito reaproveitável: interpretabilidade

O artigo propõe uma noção mais fraca e alcançável que reprodutibilidade:

> *"We call an experiment interpretable if it provides enough information to allow scientists to understand the experiment, draw own conclusions, assess their certainty, and possibly generalize results."*

> *"Exact reproduction of experiments on large parallel computers is close to impossible."*

Útil ao enquadramento: este trabalho mostra que, em treino de 3DGS, a reprodução exata é impossível **por construção numérica**, e portanto **interpretabilidade** é o padrão a perseguir. Dá vocabulário emprestado de uma referência sólida para a conclusão do Cap. 6.

## 4. Cronograma

Janela: 2026-08-26 → 06/nov/2026, **10 semanas e 2 dias**. Zero folga.

| Fase | Sem. | Período | Saída |
|---|---|---|---|
| **S0 — Bring-up e go/no-go** | 1 | 26/ago → 02/set | VkSplat treina `garden` em RDNA 4; `deviceName` e wave size confirmados; dataset baixado; decisão de escopo |
| **S1 — Pré-registro + Cap. 2** | 2-3 | 02/set → 16/set | Protocolo pré-registrado em commit; levantamento de diferenças publicadas (limiar de H2); Cap. 2 escrito |
| **S2 — Eixo 1** | 4-5 | 16/set → 30/set | N execuções concluídas; comparador de `.ply` pronto; dispersão quantificada; Cap. 4 (metodologia) escrito |
| **S3 — Eixo 2** | 6-8 | 30/set → 21/out | Intervenção determinística implementada e medida; Cap. 5 (resultados) em escrita |
| **S4 — Fechamento** | 9-10 | 21/out → 04/nov | Cap. 1, 3, 6; revisão integral; migração LaTeX; formatação ABNT |
| **Depósito** | — | **06/nov** | — |

**Cortes candidatos, escopo-base e não opções:** eixo 2 reduzido a medir apenas o custo sem a análise de erro de quantização; eixo 3 (H4) descartado; N reduzido ao mínimo defensável; segunda cena descartada.

**Hard-cap:** se o VkSplat não treinar em RDNA 4 até o fim da semana 1, o trabalho migra para a versão puramente documental — os achados categóricos de `verificacao-vulkan-rdna4.md` mais o bring-up falho documentado. Essa decisão é tomada em 02/set, não em outubro.

## 5. Sprint 0 — itens concretos

- [ ] Concluir instalação do toolchain (`build-essential`, `cmake`, `ninja-build`, `pkg-config`, `python3-venv`, `python3-dev`, `git-lfs`, `libx11-dev`)
- [ ] `usermod -aG render,video` e reinício de sessão
- [ ] Criar venv; instalar dependências do VkSplat (`numpy`, `opencv-python`, `tqdm`, `torchmetrics[image]` — puxa PyTorch, CPU basta)
- [ ] **Forkar `harry7557558/vksplat` fixando o commit `b3ad2b048918496616e0e9346e35c606d813ab55`** (auditado em 2026-08-26)
- [ ] Aplicar os **dois patches** do protocolo, cada um em commit próprio e identificável: (a) `random.seed(step)` em `simple_trainer.py:206`; (b) `RASTERIZE_BACKWARD_USE_SCHEDULING 0` em `src/config.h:24`
- [ ] Build do VkSplat (`pip install -e . --no-build-isolation`, ou CMake)
- [ ] **Confirmar `shaderBufferFloat32AtomicAdd` ativo** — é requisito de viabilidade do próprio VkSplat (`gs_pipeline.cpp`), e se cair no caminho `USE_EMULATED_F32_ATOMIC` (laço CAS em `config.slang:70-84`) o comportamento numérico muda e precisa ser declarado
- [ ] Confirmar que `SUBGROUP_SIZE 32` foi efetivamente aplicado via `VK_EXT_subgroup_size_control` — `bwd_per_pixel` depende disso (`thread_rank % SUBGROUP_SIZE == 0` em vez de `WaveIsFirstLane()`)
- [ ] **Auditar `morton_sort.slang`** — determinismo da reordenação periódica (§8)
- [ ] **Auditar `print_benchmark_results.py`** — pode conter a metodologia das 5 execuções e do IC de 90% do artigo; necessário antes de afirmar qualquer coisa sobre elas na monografia
- [ ] Baixar `360_v2.zip` (11,7 GiB, `Accept-Ranges` suportado — usar `wget -c`); confirmar que `garden/` traz `sparse/` e `images_4/`
- [ ] Primeiro treino, com `image_cache_device='gpu'` se a RAM apertar
- [ ] Registrar `deviceName`, wave size efetivo, e **tempo de um treino** — é o que dimensiona N
- [ ] Levar o plano ao Prof. Gilvan
- [ ] Atualizar `../experimentos/caderno-de-campo.md` a cada tentativa, com timestamp e erro literal

## 6. Decisões registradas

| Data | Decisão | Justificativa |
|---|---|---|
| 2026-08-25 | Permanecer em Ubuntu 24.04.4 apesar de a premissa da reinstalação ter sido falsa | 24.04.4 também está na matriz; segundo reformat custaria mais um dia por delta marginal |
| 2026-08-26 | **Abandonar o benchmarking** como gênero de trabalho | Decisão do aluno; o desenho comparativo cross-vendor era inatribuível e dependia de aluguel de GPU |
| 2026-08-26 | Formulação "MLP fundido em Vulkan" **proposta e abandonada no mesmo dia** | Verificação da superfície de API mostrou atrito incompatível com 10 semanas: forma única 16×16×16, wave64 forçado, `coopmat` não residente em `shared`, `maintenance1` ausente no Mesa instalado, e o backward não é fundido nem na tiny-cuda-nn |
| 2026-08-26 | Objeto volta a ser **renderização neural**, não superfície de API | As formulações intermediárias haviam derivado para microarquitetura de GPU, contrariando o escopo pedido |
| 2026-08-26 | **Reaproveitar o VkSplat** em vez de escrever pipeline | Ele treina, roda em Vulkan, e já emite tempo por estágio, VRAM e PSNR/SSIM/LPIPS em JSON. O bring-up em RDNA 4 é, por si, contribuição |
| 2026-08-26 | Incluir a **intervenção determinística** (eixo 2) | Sem ela o trabalho é observacional e leve para Engenharia de Computação; com ela há código autoral, causa em vez de correlação, e escopo fechado em um estágio |

## 7. Decisões pendentes

- [ ] **Validação do tema com o Prof. Gilvan** — bloqueante de fato, ainda que não de execução
- [ ] N (número de repetições): fixar no pré-registro, considerando o custo de cada treino, ainda desconhecido
- [ ] Qual estágio do backward recebe a intervenção determinística — depende de ler o código do VkSplat e do `breakdown` da primeira execução
- [ ] Segunda cena: entra ou não
- [ ] Como levantar as "diferenças reportadas como ganho" na literatura de 3DGS para fixar o limiar de H2, sem transformar isso em revisão sistemática

## 8. Riscos e ameaças à validade

| Risco | Impacto | Mitigação |
|---|---|---|
| **(2026-08-26) O VkSplat pode ter eliminado as atômicas por pixel** | Ameaça direta a H3a | **RESOLVIDO pela auditoria do commit `b3ad2b0`: as atômicas em `float32` permanecem.** São **9 sítios de `_ATOMIC_ADD` por implementação, 27 no total**, sobre os mesmos 4 tensores da versão CUDA — `v_xy_vs`, `v_inv_cov_vs_opacity[0..2]`, `v_inv_cov_vs_opacity[3]`, `v_rgb`. O redesenho descrito no artigo mudou a **granularidade** (contenção, problema de desempenho), não a **natureza** da acumulação. A pré-redução por subgrupo (`WaveActiveSum`) e por memória compartilhada é determinística *localmente*; a combinação final entre workgroups continua atômica e sem ordem imposta pelo código |
| **(2026-08-26) Seleção entre kernels de backward por amostragem de Thompson guiada por latência medida** | Segunda fonte de não-determinismo, dependente de carga da máquina; contamina a série de N execuções | **Mitigável e mitigado no protocolo:** `RASTERIZE_BACKWARD_USE_SCHEDULING 0` em `src/config.h:24` + recompilação da extensão, o que fixa a implementação `PerSplat`. Não há variável de ambiente nem opção de config — é patch de compilação, e por isso entra no pré-registro com commit do fork. Em AMD o escalonador alterna entre `PerSplat` (autodiff) e `Tensor_0_8_8` (formulação em espaço-log), que **não são numericamente equivalentes**: formulação distinta, ordem de redução distinta, compilação com `-fp-mode fast`, e divergência literal no guarda de limiar de alpha (`<=` contra `>=`) no ponto `a == 1/255` |
| **(2026-08-26) A seed não é fixável de ponta a ponta** | A ordem de visitação das imagens difere entre execuções, o que altera o **conteúdo** dos gradientes e não apenas a ordem de soma — fonte que precede as atômicas | Patch de uma linha: descomentar `random.seed(step)` em `simple_trainer.py:206`. O lado GPU já é determinístico — `rng.seed(42)` hard-coded em `gs_trainer.cpp:127`, alimentando inicialização de quatérnions, densificação default, MCMC e ruído SGLD, todos com RNG *counter-based* sem estado. Não há campo `seed` em nenhum `TrainerConfig` nem nos bindings; os dois patches são a razão de o fork com commit fixado ser obrigatório |
| **(2026-08-26) Reordenação Morton periódica** (`step % refine_every == 0`) muda os índices de destino das atômicas | Se a reordenação não for determinística, é fonte adicional que pode sobreviver a D3 e falsificar H3a | **Não auditado.** Item de Sprint 0: verificar `morton_sort.slang`. O radix sort principal **é** determinístico e estável (ranking por ballot, slots disjuntos, atômicos apenas inteiros) |
| **`llvmpipe` enumerado como 2º dispositivo Vulkan** | Uma execução cai em rasterizador de CPU e produz números absurdos; contamina a série | Fixar seleção de dispositivo; registrar `deviceName` em toda saída; o harness falha alto se não for a GPU esperada |
| **(2026-08-26) Convenção de normalização do LPIPS** — o pipeline de avaliação herdado do 3DGS normaliza com estatísticas de faixa [−1,1] passando imagens em [0,1], o que torna o LPIPS reportado sistematicamente mais favorável e **não comparável** entre convenções | Atinge **H4** diretamente: comparar LPIPS obtido com LPIPS publicado por terceiros pode ser inválido | Declarar a convenção usada no pré-registro; verificar qual o `torchmetrics` aplica no caminho do VkSplat; se necessário, reportar as duas |
| **`llvmpipe` enumerado como 2º dispositivo Vulkan** | Uma execução cai em rasterizador de CPU e produz números absurdos; contamina a série | Fixar seleção de dispositivo; registrar `deviceName` em toda saída; o harness falha alto se não for a GPU esperada |
| **Wave size não fixado** | RADV pode compilar em wave64 por padrão; layout e alinhamento mudam; mede-se duas coisas crendo medir uma | Fixar explicitamente e declarar qual foi usado |
| **VkSplat nunca testado em RDNA 4** | Bring-up pode não fechar | É o hard-cap da semana 1; falha documentada é resultado (N0) |
| **15 GiB de RAM com `image_cache_device='cpu'`** | OOM no carregamento do dataset | Usar `'gpu'` (16 GB de VRAM); `images_4`; uma cena |
| **Shaders podem exigir recompilação** (`USE_EMULATED_F32_ATOMIC`) | Requer toolchain Slang, ausente do apt | Baixar Slang preventivamente. **Se o caminho emulado for acionado, o objeto de estudo muda** e isso precisa ser declarado, não contornado |
| **Viés de confirmação já se materializou neste projeto** (2026-08-25) | Aqui o incentivo é direto: o aluno quer que a dispersão seja grande, porque dispersão grande é o achado interessante | Pré-registro dos limiares **antes** de medir; escrutínio maior para resultados que favorecem a tese |
| **(2026-08-26) H2 pode nascer refutada — a dispersão pode ser menor que o limiar** | Evidência contrária ao esperado: em `gsplat` #872, as execuções 2–5 numa mesma máquina mostram amplitude de PSNR de **~0,07 dB**; e o σ publicado pelo 3DGS-MCMC é **0,0276 dB** (init SfM, nível de dataset, seed variável). O limiar de H2 está em **0,10 dB**. **A dispersão pode ficar abaixo dele** | **Isto é resultado válido e está declarado como tal antes de medir** (ver linha abaixo). Duas notas técnicas que preservam a pergunta: (a) os σ publicados são de **média sobre 7 cenas**; a dispersão **por cena** — que é o que este trabalho mede, em `garden` — é maior, e o σ por cena seria da ordem de 0,07–0,14 dB se as cenas fossem independentes (inferência, não valor publicado); (b) a comparação relevante é por cena contra o menor delta por cena, não médias contra médias. **Fixar isso no pré-registro antes de medir** |
| **Dispersão pode ser pequena** | H1/H2 refutadas; o achado "interessante" desaparece | **Isso é resultado válido e deve ser escrito como tal.** "Treino de 3DGS é reprodutível dentro de X dB" é informação útil e publicável, e responde a uma pergunta aberta desde 2023 que ninguém quantificou. Declarar isso agora, por escrito, é o que impede o ajuste posterior do limiar |
| **A causa pode não ser a atômica** | H3 refutada | Passa a ser o achado: enumerar as outras fontes candidatas (ordem de redução, seleção de kernel, alocador) |
| **Ponto fixo pode degradar qualidade** | Intervenção "funciona" mas piora o modelo | É o *trade-off* determinismo × qualidade, e é resultado |
| **N execuções × custo por treino desconhecido** | Cronograma de S2 estoura | Medir o custo de um treino na semana 1 e dimensionar N a partir disso, antes do pré-registro |
| **Configuração fora da combinação literal da matriz ROCm** (24.04.4 com kernel HWE 7.0) | Irrelevante aqui: ROCm está fora do caminho crítico | Declarar no Cap. 4 por completude |
| **Zero papers lidos** das 62 entradas do fichamento antigo, e a triagem descartou 27 | Cap. 2 e 3 sem base | A bibliografia do tema novo precisa ser construída: reprodutibilidade em ML, determinismo em GPU, aritmética de ponto flutuante não-associativa, prática de reporte em 3DGS |
| **Janela de 10 semanas e 2 dias, após três reenquadramentos em uma semana** | Depósito atrasa | Cortes de §4 são escopo-base; hard-cap na semana 1; escrita começa na semana 2 e não espera o experimento |

## 9. Estado atual (2026-08-26)

- **Nada escrito** de monografia. **Nada executado** de pipeline.
- Ambiente: Ubuntu 24.04.4, kernel HWE `7.0.0-30`, RX 9070 XT (`gfx1201`) confirmada pelo RADV, Mesa 25.2.8, `vulkan-tools` instalado. Toolchain de build **em instalação**. Usuário ainda fora de `render`/`video`.
- Instrumentação de potência disponível via `sysfs`/hwmon, embora não seja mais métrica deste tema.
- `VK_KHR_cooperative_matrix` presente (revision 2) — não é mais objeto do trabalho, mas os achados coletados sobre a superfície de API estão preservados em `bibliografia/verificacao-vulkan-rdna4.md` e permanecem citáveis.
- **Verificado sobre o VkSplat:** treina 3DGS do zero; pede `VK_API_VERSION_1_2` (compatível com o loader 1.3.275); requer `VK_EXT_subgroup_size_control` e `VK_EXT_shader_atomic_float`; lê **somente** COLMAP; emite `train.json`/`eval.json` com breakdown por estágio; publicado em Eurographics 2026 Short Papers (DOI 10.2312/egs.20261024); `pushed_at` 2026-08-21; **0 issues** desde a criação; testado até RX 7800 XT (RDNA 3).
- **Verificado sobre o `taichi-ngp-renderer`:** só inferência, sem treino. Fora deste tema.
- Bibliografia do tema novo: **a construir**.

## 10. Materiais

| Caminho | Conteúdo |
|---|---|
| `CLAUDE.md` (esta pasta) | Papel do assistente, tema, armadilhas técnicas, disciplina de método |
| `PLANO.md` (este arquivo) | Fonte de verdade do enquadramento |
| `bibliografia/verificacao-vulkan-rdna4.md` | Fatos verificados sobre Vulkan/RADV/RDNA 4, com fonte e data. Inclui material da formulação abandonada, ainda citável |
| `../PLANO.md`, `../CLAUDE.md` | Tema anterior; **registro histórico, não apagar** |
| `../bibliografia/fichamento.md` | 62 entradas, 60 referências distintas. Triagem de 2026-08-26 sob a formulação anterior; **precisa de nova triagem para este tema** |
| `../bibliografia/verificacao-experimento-rdna4.md` | Fonte de verdade do tema anterior; §3 (VkSplat) segue central |
| `../experimentos/00-inventario/saidas/` | Dois inventários datados (26.04 e 24.04.4) |
| `../experimentos/caderno-de-campo.md` | Log de bring-up: tentativas, falhas e classificação |
