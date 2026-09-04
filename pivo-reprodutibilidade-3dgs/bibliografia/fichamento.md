# Fichamento — reprodutibilidade em treino de 3DGS

> **Estado: em construção.** Iniciado em 2026-08-26. Substitui, para o tema atual, o `../../bibliografia/fichamento.md`, construído para o tema de benchmarking.

## Como usar este arquivo

O campo `status_validacao` rastreia **verificação de metadados em fonte primária** — não leitura:

| Status | Significado |
|---|---|
| `validado_doi` | DOI conferido no Crossref ou na página do venue |
| `validado_arxiv` | Identificador conferido na API oficial do arXiv |
| `validado_doc_oficial` | Documentação oficial de fornecedor ou organismo de padronização |
| `validado_github` | Repositório conferido via `api.github.com` |
| `fonte_primaria_inacessivel` | Existência confirmada, texto integral não obtido — **não citar conteúdo específico** |
| `incerto` | Metadados não conferidos — **não citar** |

> **Observação metodológica do orientador:** este é um *mapa de leitura*, **não substitui a leitura das fontes**. **Nenhuma entrada está lida.** O caso mais concreto disso está em E.1: os metadados estão validados, mas o conteúdo (as "doze regras") não foi lido e por isso não pode ser enunciado.

Eixos: **A** renderização neural e o objeto · **B** ponto flutuante e somatório reprodutível · **C** reprodutibilidade em ML e prática de reporte · **D** plataforma · **E** metodologia e métricas.

---

## Eixo A — Renderização neural: fundamentos e o objeto de estudo

### A.1 — Kerbl, Kopanas, Leimkühler, Drettakis (2023) — 3D Gaussian Splatting [validado_doi + validado_arxiv]
- **Venue:** ACM Transactions on Graphics 42(4), pp. 1–14 (SIGGRAPH 2023) · DOI `10.1145/3592433` · arXiv 2308.04079
- **URL:** <https://doi.org/10.1145/3592433> · <https://arxiv.org/abs/2308.04079> — acesso 2026-08-26
- **Ideia-chave:** gaussianas 3D anisotrópicas com rasterizador diferenciável por tiles; qualidade de estado da arte em tempo real, sem MLP.
- **Relevância:** referência do objeto de estudo. Financiamento ERC 788065 (FUNGRAPH).
- **⚠ Grafia:** Crossref/ACM registram **"Leimkuehler"**; arXiv registra **"Leimkühler"**. Padronizar e declarar a escolha.
- **Onde citar:** Cap. 2; Cap. 4.

### A.2 — Ye; Kanazawa (2023) — Mathematical Supplement for the gsplat Library [validado_arxiv]
- **arXiv:** 2312.02121 (v1 2023-12-04), cs.MS/cs.CV/cs.GR/math.NA
- **URL:** <https://arxiv.org/abs/2312.02121> — acesso 2026-08-26
- **Ideia-chave:** *"a self-contained reference for the computations involved in the forward and backward passes of differentiable Gaussian splatting."*
- **Relevância:** **é a referência citável para a derivação do backward** — onde ficam as acumulações atômicas de gradiente que a intervenção substitui. Provavelmente a citação mais útil do Cap. 4.
- **Onde citar:** Cap. 4 (implementação).

### A.3 — Chen, Ibrahim, Liu (2026) — VkSplat [validado_arxiv + validado_github]
- **Venue:** Eurographics 2026 — Short Papers · DOI `10.2312/egs.20261024` · arXiv 2605.00219 (v1 2026-04-30)
- **Repositório:** `harry7557558/vksplat` — 144 stars, `pushed_at` 2026-08-21, Apache-2.0, **0 issues desde a criação**
- **Ideia-chave:** treino completo de 3DGS em Vulkan compute. Alega 3,3× sobre gsplat e **paridade de qualidade** (*"identical PSNR, SSIM, LPIPS compared to GSplat"*).
- **Relevância:** implementação usada no experimento. Requer `VK_EXT_subgroup_size_control` e `VK_EXT_shader_atomic_float`; pede `VK_API_VERSION_1_2`; lê **somente** COLMAP; emite `train.json` com breakdown por estágio e `eval.json` com PSNR/SSIM/LPIPS.
- **⚠ Ressalva vinculante:** testados NVIDIA 3090/4080S/5070 Laptop, **AMD RX 7800 XT (RDNA 3)**, Intel UHD. **RDNA 4 não consta.**
- **Correção de registro:** `../../bibliografia/verificacao-experimento-rdna4.md` §3 dizia "submitted, não aceito" — **desatualizado**, foi publicado com DOI.

### A.4 — Ye, Li, Kerr, Turkulainen, Yi, Pan, Seiskari, Ye, Hu, Tancik, Kanazawa (2024) — gsplat [validado_arxiv]
- **arXiv:** 2409.06765 (v1 2024-09-10) · comentário dos autores indica **JMLR MLOSS** — **venue não confirmado por DOI**
- **Ideia-chave:** front-end Python/PyTorch com back-end de kernels CUDA otimizados, Apache-2.0.
- **Relevância:** é o baseline contra o qual o VkSplat se compara, e um caminho alternativo de implementação da variante determinística — licença permissiva e backward documentado em A.2.

### A.5 — Mildenhall, Srinivasan, Tancik, Barron, Ramamoorthi, Ng (2020) — NeRF [validado_arxiv]
- **arXiv:** 2003.08934 (v1 2020-03-19, v2 2020-08-03) · ECCV 2020 (oral)
- **Relevância:** linhagem em que o 3DGS se insere; fonte do dataset NeRF-synthetic, **não** utilizável diretamente pelo VkSplat.

### A.6 — Barron et al. (2022) — Mip-NeRF 360 [incerto]
- **Status:** metadados **não reconferidos**. Existe no fichamento antigo (B.5) como `validado_arxiv`, identificador não transcrito.
- **Relevância:** fonte do dataset primário (cena `garden`, `images_4`). **Não citar até reconferir.** Verificação em curso.

---

## Eixo B — Ponto flutuante, determinismo e somatório reprodutível

> Eixo que sustenta o **mecanismo** da pesquisa.

### B.1 — Higham (2002) — Accuracy and Stability of Numerical Algorithms, 2ª ed. [validado_doi]
- **Editora:** SIAM · DOI `10.1137/1.9780898718027` · ISBN 9780898715217 (impresso), 9780898718027 (eletrônico)
- **Relevância:** referência canônica de análise de erro de arredondamento; o Cap. 4 trata de somatório. Fundamenta a cota de erro do somatório recursivo e **por que a ordem de acumulação altera o resultado** — base teórica do mecanismo.
- **Onde citar:** Cap. 2 (fundamentação numérica).

### B.2 — IEEE (2019) — IEEE Std 754-2019 [validado_doc_oficial + validado_doi]
- **DOI** `10.1109/IEEESTD.2019.8766229` · ISBN 9781504459242 · aprovado 2019-06-13, publicado 2019-07-22 · **supersede 754-2008** · status *Active*
- Equivalente internacional: **ISO/IEC/IEEE 60559:2020**
- **Relevância:** define `binary32`, modos de arredondamento, e o fato de cada operação ser individualmente determinística — o que **localiza a indeterminação na ordem, não na aritmética**.
- **⚠ Ressalva:** a norma **não afirma** não-associatividade explicitamente; isso é consequência do arredondamento por operação. Para afirmação textual direta, usar C.1.

### B.3 — Demmel; Nguyen (2013) — Fast Reproducible Floating-Point Summation [validado_doi]
- ARITH-21, pp. 163–172 · DOI `10.1109/ARITH.2013.9`
- **Ideia-chave:** somatório reprodutível independente de ordem e de número de processadores, em uma passagem, por pré-arredondamento em *bins* de expoente.
- **Relevância:** trabalho-referência do problema exato do TCC, e **contraponto técnico à solução por ponto fixo** — serve para justificar a escolha de projeto em vez de apresentá-la como única.

### B.4 — Demmel; Nguyen (2015) — Parallel Reproducible Summation [validado_doi]
- IEEE Transactions on Computers 64, pp. 2060–2070 · DOI `10.1109/TC.2014.2345391`
- **Relevância:** versão de revista com análise de erro e **custo** em ambiente paralelo. Precedente quantificado de overhead de reprodutibilidade, para contextualizar a medição do eixo 2.

### B.5 — Ahrens; Demmel; Nguyen (2020) — Algorithms for Efficient Reproducible Floating Point Summation [validado_doi]
- ACM TOMS, pp. 1–49 · DOI `10.1145/3389360` (2020-07-21)
- **Relevância:** tratamento mais maduro da linha. **Citação preferencial** quando bastar uma referência da abordagem Berkeley.

### B.6 — Collange; Defour; Graillat; Iakymchuk (2015) — Numerical reproducibility for the parallel reduction on multi- and many-core architectures [validado_doi]
- Parallel Computing 49, pp. 83–97 · DOI `10.1016/j.parco.2015.09.001`
- **Relevância:** **referência central do eixo.** Acumulador longo / superacumulador aplicado a **redução paralela em GPU**, combinando *error-free transformations* com precisão estendida para reprodutibilidade independente de ordem. A acumulação em ponto fixo proposta no TCC é uma versão simplificada e barata desta ideia — enquadrar assim, explicitamente.

### B.7 — Iakymchuk; Defour; Collange; Graillat (2016) — Reproducible and Accurate Matrix Multiplication [validado_doi]
- LNCS, *Scientific Computing, Computer Arithmetic, and Validated Numerics*, pp. 126–137 · DOI `10.1007/978-3-319-31769-4_11`
- **Relevância:** mostra que a abordagem generaliza a BLAS-3. Secundária.

### B.8 — Iakymchuk; Graillat; Defour; Quintana-Ortí (2019) — Hierarchical approach for deriving a reproducible unblocked LU factorization [validado_doi]
- IJHPCA, pp. 791–803 · DOI `10.1177/1094342019832968`
- **Relevância:** complementar; citar só para mostrar amplitude do programa de pesquisa.

### B.9 — Kahan (1965) — Pracniques: further remarks on reducing truncation errors [validado_doi]
- Communications of the ACM 8(1), p. 40 · DOI `10.1145/363707.363723`
- **⚠ Título:** o registro inclui o prefixo **"Pracniques:"**, quase sempre omitido nas citações. É nota de **uma página**.
- **Relevância:** origem do somatório compensado. No TCC serve para a distinção crítica: compensação melhora **acurácia** e **não garante reprodutibilidade** sob ordem variável.

### B.10 — Neumaier (1974) — Rundungsfehleranalyse einiger Verfahren zur Summation endlicher Summen [validado_doi]
- ZAMM 54(1), pp. 39–51 · DOI `10.1002/zamm.19740540106` · **em alemão**
- **Relevância:** origem da variante Kahan–Babuška–Neumaier. Compara cotas *a priori* de erro para vários métodos de somatório. Citar pelo conteúdo verificado, não por resumo de terceiro.

### B.11 — Ogita; Rump; Oishi (2005) — Accurate Sum and Dot Product [validado_doi]
- SIAM Journal on Scientific Computing 26(6), pp. 1955–1988 · DOI `10.1137/030601818`
- **Relevância:** referência canônica de **error-free transformations** (`TwoSum`, `TwoProduct`), usando apenas operações na precisão nativa, sem desvios e sem acesso a mantissa/expoente — propriedades que importam em kernel de GPU. Base algorítmica dos superacumuladores.

---

## Eixo C — Reprodutibilidade em ML e prática de reporte

### C.1 — PyTorch Contributors — Reproducibility (documentação oficial) [validado_doc_oficial]
- **URL:** <https://docs.pytorch.org/docs/stable/notes/randomness.html> — acesso 2026-08-26 (página datada 2026-05-14; `stable` = série 2.13)
- **Relevância:** **melhor fonte primária para o mecanismo do TCC.** Três afirmações verificadas textualmente:
  1. *"Each backend performs floating-point accumulation in a different order, and because **floating-point addition is not associative**, the results will differ between backends."*
  2. O backward de `SDPBackend.FLASH_ATTENTION` é classificado **Non-deterministic**: *"The backward pass uses **non-deterministic atomic operations** by default."*
  3. *"Deterministic operations are often slower than nondeterministic operations"* — reconhecimento oficial do trade-off que o eixo 2 vai medir.
- Documenta `torch.use_deterministic_algorithms()`, `torch.backends.cudnn.benchmark/deterministic`, e o não-determinismo por *benchmarking* de algoritmo do cuDNN.
- **Delimitação da contribuição:** o rasterizador do 3DGS é kernel customizado **fora** da cobertura desse flag.

### C.2 — Zhuang; Zhang; Song; Hooker (2021) — Randomness In Neural Network Training: Characterizing The Impact of Tooling [validado_arxiv]
- **arXiv:** 2106.11872 (v1 2021-06-22), cs.LG · código em `github.com/usyd-fsalab/NeuralNetworkRandomness`
- **Ideia-chave:** métricas agregadas como top-1 quase não mudam, mas **partes da distribuição dos dados são muito mais sensíveis** à aleatoriedade; o custo de eliminar não-determinismo chega a **746%, 241% e 196%** de overhead em diferentes GPUs.
- **Relevância:** **precedente metodológico direto** — medir dispersão e medir o custo do determinismo é exatamente o desenho do TCC. Referência de comparação para o overhead medido.

### C.3 — Summers; Dinneen (2021) — Nondeterminism and Instability in Neural Network Optimization [validado_arxiv]
- **arXiv:** 2103.04514 (v3 2021-03-08) · comentário indica **ICML 2021** — venue **não confirmado por DOI**
- **Ideia-chave:** todas as fontes de não-determinismo têm efeito similar sobre diversidade de modelos, explicado pela **instabilidade** do treino: *"even one-bit changes in initial parameters result in models converging to vastly different values."*
- **Relevância: é ameaça ao enquadramento, não apoio, e precisa ser enfrentada explicitamente.** Obrigou a separar, no `PLANO.md` §2.3, **repetibilidade** de **estabilidade** — ver H3a e H3b.

### C.4 — Pham, Qian, Wang, Lutellier, Rosenthal, Tan, Yu, Nagappan (2020) — Problems and opportunities in training deep learning software systems [validado_doi]
- ASE 2020, pp. 771–783 · DOI `10.1145/3324884.3416545`
- **⚠ Divergência:** o Crossref registra o título **sem** o subtítulo *"an analysis of variance"*, presente na maioria das citações. Conferir o campo na página do ACM DL antes de citar.
- **Relevância:** estudo empírico de variância entre execuções, pela ótica de Engenharia de Software — enquadra o problema como defeito de software, não só numérico.

### C.5 — Bouthillier, Delaunay, Bronzi, Trofimov, Nichyporuk, Szeto, Sepah, Raff, Madan, Voleti, Kahou, Michalski, Serdyuk, Arbel, Pal, Varoquaux, Vincent (2021) — Accounting for Variance in Machine Learning Benchmarks [validado_arxiv]
- **arXiv:** 2103.03098 (v1 2021-03-01) · comentário indica *submitted to MLSys 2021* — **não confirmado**
- **Relevância:** **a referência para "dentro do ruído".** Modela o processo de benchmarking inteiro, mostra que variância por amostragem, inicialização e hiperparâmetros afeta resultados de forma marcante, e propõe recomendações de comparação. Casa com H2.

### C.6 — Melis; Dyer; Blunsom (2017) — On the State of the Art of Evaluation in Neural Language Models [validado_arxiv]
- **arXiv:** 1707.05589 (v2 2017-07-18), cs.CL
- **Ideia-chave:** com busca de hiperparâmetros em larga escala, **LSTMs padrão bem regularizadas superam modelos mais recentes** — ganhos reportados vinham de variação experimental não controlada.
- **Relevância:** **precedente retórico** do argumento central: caso concreto e muito citado de "a diferença estava no ruído".

### C.7 — Pineau, Vincent-Lamarre, Sinha, Larivière, Beygelzimer, d'Alché-Buc, Fox, Larochelle (2020) — Improving Reproducibility in Machine Learning Research [validado_arxiv]
- **arXiv:** 2003.12206 (v4 2020-03-27) · comentário: *"To appear at JMLR"* — **volume/número não confirmados**
- **Relevância:** referência institucional (programa de reprodutibilidade do NeurIPS 2019, ML Reproducibility Checklist). A checklist dá critérios concretos para o Cap. 4.

### C.8 — Gundersen; Kjensmo (2018) — State of the Art: Reproducibility in Artificial Intelligence [validado_doi]
- AAAI 32 · DOI `10.1609/aaai.v32i1.11503` (2018-04-25)
- **Relevância:** taxonomia de graus de reprodutibilidade. Argumento forte para a introdução: **mesmo com código e dados idênticos — o grau mais forte da taxonomia — o resultado ainda diverge por causa do hardware.**

### C.9 — Raff (2019) — A Step Toward Quantifying Independently Reproducible Machine Learning Research [validado_arxiv]
- **arXiv:** 1909.06674 (v1 2019-09-14) · comentário indica NeurIPS 2019
- **Ideia-chave:** tentativa manual de implementar **255 artigos (1984–2017)** deliberadamente **sem olhar o código dos autores**, com análise dos fatores que predizem reprodutibilidade.
- **Relevância:** contraponto — liberar código é necessário e não suficiente.

---

## Eixo D — Plataforma: Vulkan, atômicos e RDNA 4

> Fatos verificados desta área em `verificacao-vulkan-rdna4.md`, com fonte e data por afirmação.

### D.1 — Khronos Group (2020) — VK_EXT_shader_atomic_float [validado_doc_oficial]
- **Registry Vulkan:** extensão nº **261**, revisão **1**, Last Modified **2020-07-15**, status **Ratified**
- Dependência SPIR-V: `SPV_EXT_shader_atomic_float_add`; capabilities `AtomicFloat32AddEXT`/`AtomicFloat64AddEXT`; operação `OpAtomicFAddEXT`. Contato Vikram Kushwaha (NVIDIA); contribuidores Kushwaha e Jeff Bolz. Fornece suporte de API a `GL_EXT_shader_atomic_float`
- **URL:** <https://registry.khronos.org/vulkan/specs/latest/man/html/VK_EXT_shader_atomic_float.html> — acesso 2026-08-26
- **Relevância:** **é o mecanismo central**, requerido incondicionalmente pelo VkSplat em `createDevice()`. Dois usos argumentativos: (a) adição atômica em float é recurso **opcional e relativamente recente**, enquanto atômicos **inteiros** são funcionalidade central — argumento de portabilidade a favor da variante em ponto fixo; (b) fundamento da seção de implementação.

### D.2 — NVIDIA — CUDA C++ Programming Guide, §7.14 Atomic Functions [validado_doc_oficial]
- **URL:** <https://docs.nvidia.com/cuda/archive/12.6.0/cuda-c-programming-guide/index.html#atomic-functions> — acesso 2026-08-26
- **Relevância:** semântica, escopo e ordenação do atômico: *read-modify-write* em 32/64/128 bits, ordenação `cuda::memory_order_relaxed`, escopos `_system`/device/`_block`.
- **⚠ Ressalva deliberada:** a seção **não afirma** não-associatividade nem não-determinismo de `atomicAdd`. **Não citar para essa finalidade** — usar C.1.

### D.3 — Mesa 25.2.8 — código-fonte do RADV [validado_doc_oficial]
- **Fonte:** `https://archive.mesa3d.org/mesa-25.2.8.tar.xz` — acesso 2026-08-26
- **Relevância:** versão do driver que roda o experimento; **fonte primária de comportamento**. Fatos já extraídos: cooperative matrix exige backend ACO (`radv_physical_device.c:147-150`); wave size forçado a 64 sob certas condições (`radv_shader_info.c:928-941`, `RADV_SUBGROUP_SIZE = 64`); alinhamento de load dependente do wave size.

### D.4 — Khronos Group (2023) — VK_KHR_cooperative_matrix [validado_doc_oficial]
- Extensão nº 507, revisão 2, Last Modified 2023-05-03, **Ratified**
- **Relevância: periférica.** Mantida porque os achados categóricos derivados (esparsidade SWMMAC inalcançável; BF16 recusado em gfx11 por imprecisão de hardware; `maintenance1` ratificada e ausente no Mesa instalado) são observações verificáveis sobre o ecossistema, citáveis como contexto no Cap. 5. **Não é objeto do trabalho.**

---

## Eixo E — Metodologia de medição e métricas

### E.1 — Hoefler; Belli (2015) — Scientific benchmarking of parallel computing systems: twelve ways to tell the masses when reporting performance results [validado_doi · **LIDO 2026-09-01**]
- **SC15**, Austin, Texas, pp. 1–12, ACM · DOI `10.1145/2807591.2807644` · publicado 2015-11-15 · 64 referências · ambos os autores do Dept. of Computer Science, ETH Zurich
- **Cópia de autor lida:** <https://spcl.inf.ethz.ch/Publications/.pdf/hoefler-scientific-benchmarking.pdf>, alcançada pela página de publicações do SPCL (<https://spcl.inf.ethz.ch/Publications/index.php?pub=222>) — acesso 2026-09-01. Disponibilizada pelo grupo do primeiro autor, com nota de disseminação acadêmica não-comercial.
- **Metadados corrigidos** em relação ao fichamento antigo (E.5, que estava `incerto`): **exatamente dois autores**; **ano 2015, SC15**, não periódico; o **subtítulo integra o título** e entra após dois-pontos na ABNT.
- **⚠ Ressalva de citação.** A cópia do SPCL **não é idêntica** ao proceedings de 2015: traz `© 2017 Copyright held by the owner/author(s)` e ao menos uma correção datada — a nota de rodapé 3, marcada *"Update 2017/01/25 (thanks to S. Rinke)"*, que reescreve a interpretação do intervalo de confiança. O resumo também difere levemente. **Se citar a nota 3 literalmente, ela vem da versão de autor corrigida, não do proceedings de 2015.** Declarar isso.
- **Ideia-chave:** doze regras para reportar desempenho de forma interpretável, e a noção de **interpretabilidade** — mais fraca que reprodutibilidade e alcançável: *"enough information to allow scientists to understand the experiment, draw own conclusions, assess their certainty, and possibly generalize results."*
- **Regras que sustentam este TCC:**
  - **Rule 5** — *"Report if the measurement values are deterministic. For nondeterministic data, report confidence intervals of the measurement."* Fundamenta o trabalho inteiro.
  - **Rule 6** — *"Do not assume normality of collected data (e.g., based on the number of samples) without diagnostic checking."*
  - **Rule 7** — *"Compare nondeterministic data in a statistically sound way, e.g., using non-overlapping confidence intervals or ANOVA."*
  - **Rule 8** — investigar se média ou mediana são úteis; alguns problemas exigem outros percentis.
  - **Rule 9** — documentar todos os fatores variáveis e o setup completo.
  - **Rule 11** — mostrar limites superiores para dar interpretabilidade. **Reinterpretada** aqui como o teto determinístico (degrau D3).
  - **Rule 12** — plotar informação suficiente; só ligar pontos por linha se houver tendência interpolável.
- **Dado citável para a introdução:** levantamento de **95 artigos de HPC** em que **apenas 15 mencionam alguma medida de variância** e **apenas 2 reportam intervalo de confiança em torno da média**; e *"51 out of 95 applicable papers use summarizing to present results. Only four of these specify the exact averaging method."*
- **Afirmação que exige cuidado ao transferir:** o artigo justifica a não-normalidade em medição de computador por mecanismo direcional — *"most system effects lead to increased execution times... typically leading to multi-modal distributions that are heavily skewed to the right"*. **Esse mecanismo não transfere** para acumulação atômica não-associativa, que não tem direção privilegiada a priori. Citar a Rule 6 sem herdar a justificativa, e dizer isso no texto.
- **O que o artigo NÃO cobre:** *bootstrap* — *"More advanced statistical techniques such as bootstrap are beyond the scope of our work."* Não ancorar bootstrap aqui; usar Davison e Hinkley ou Efron e Tibshirani.
- **Consequências operacionais** em `../PLANO.md` §3.5: critério de parada sequencial, CI não-paramétrico da mediana (fórmula que o artigo atribui a Le Boudec), política de outliers, e dimensionamento de N.
- **Onde citar:** Cap. 3 ou 4 (metodologia); Cap. 1 (o dado dos 95 artigos); Cap. 6 (interpretabilidade).

### E.2 — Métricas: PSNR, SSIM, LPIPS [incerto]
- SSIM: Wang, Bovik, Sheikh, Simoncelli (2004) — `fonte_primaria_inacessivel` no fichamento antigo (A.12)
- LPIPS: Zhang, Isola, Efros, Shechtman, Wang (2018) — `validado_arxiv` no antigo (A.8), identificador não transcrito
- PSNR: métrica clássica, precisa de fonte citável adequada
- **Verificação em curso.** São as três métricas cuja dispersão será medida; não é aceitável reportá-las sem referência de definição.

---

## Lacunas conhecidas

1. **O limiar de H2 não existe ainda.** Falta o levantamento de deltas de PSNR que a literatura de 3DGS trata como ganho, e a contagem de quantos desses trabalhos reportam dispersão. **Bloqueia o pré-registro.** Em verificação.
2. **Originalidade não estabelecida.** Busca no arXiv (`abs:"Gaussian Splatting" AND abs:"deterministic"`, 35 resultados, 15 revisados) não encontrou nada sobre reprodutibilidade numérica de treino — todos usam "deterministic" em outro sentido. **Insuficiente para afirmar novidade.** Falta: IEEE Xplore, ACM DL, Eurographics Diglib (EGSR, i3D), e — provavelmente o mais produtivo — **issues e pull requests** de `graphdeco-inria/gaussian-splatting` e `nerfstudio-project/gsplat`, porque não-determinismo aparece primeiro como issue, não como artigo. Termo adicional: "bitwise reproducibility".
3. **ExBLAS e ReproBLAS não têm artigo homônimo indexado.** Não inventar "ExBLAS (20xx)". O método está em B.6 (ExBLAS) e B.3–B.5 (ReproBLAS). Se precisar citar o software, citar repositório com versão/commit. Procurar em HAL (`hal.science`), Software Heritage, Zenodo.
4. **Whitepaper da NVIDIA sobre conformidade IEEE 754 em GPUs** (usualmente atribuído a Whitehead e Fit-Florea) **não verificado** — sem autores, data ou URL confirmados. Procurar em `docs.nvidia.com/cuda/floating-point/`. Alternativa já validada e mais forte: C.1.
5. **Análogo AMD/ROCm de atômicos e determinismo** não pesquisado. Procurar HIP Programming Guide em `rocm.docs.amd.com`, e `VK_EXT_shader_atomic_float2` no registry.
6. **Subtema "significância estatística em comparações de deep learning" com cobertura rasa.** C.5 e C.6 estão validados; candidatos canônicos **não verificados**: Reimers & Gurevych (*Reporting Score Distributions Makes a Difference*, EMNLP 2017), Dodge et al. (*Show Your Work*), Henderson et al. (*Deep RL that Matters*), Lucic et al. (*Are GANs Created Equal?*). **Não citar antes de verificar.** ACL Anthology dá metadados melhores que o arXiv para os de NLP.
7. **Quatro entradas validadas só como preprint**, com venue vindo de comentário dos autores e não de registro independente: C.7 (JMLR), C.3 (ICML 2021), C.5 (MLSys 2021), A.4 (JMLR MLOSS). Para ABNT, preferir a versão publicada. Procurar em `jmlr.org/papers`, `proceedings.mlr.press`, `proceedings.mlsys.org`.
8. **Zero fontes lidas.** Todas as entradas rastreiam metadados.
9. O fichamento antigo precisa de **nova triagem** para este tema — a de 2026-08-26 foi feita sob a formulação do MLP fundido, abandonada.
