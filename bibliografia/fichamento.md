# Fichamento Bibliográfico — Estado da Arte

**TCC:** Renderização Neural em Hardware Heterogêneo — Portabilidade e desempenho de NeRF/3DGS em GPUs AMD RDNA 4 (RX 9070 XT)
**Aluno:** Fabio Gabriel — Eng. Computação UFC
**Orientador:** Prof. Gilvan
**Data inicial deste fichamento:** 2026-06-23

---

## Como usar este arquivo

Este é o **fichamento bibliográfico vivo** do TCC. Cada entrada contém:

- `chave_abnt` — chave de citação no padrão ABNT autor-data (ex.: `MILDENHALL et al. (2020)`)
- `autores`, `título`, `ano`, `venue` — metadados para a referência completa em ABNT NBR 6023
- `arxiv_id` / `url_primária` — onde validar
- `ideia_chave` — síntese de 1-2 frases (em português)
- `relevância_tcc` — por que importa para esta pesquisa específica
- `onde_citar` — capítulo provável da monografia
- `status_validacao`:
  - `validado_arxiv` — preprint conferido em arxiv.org
  - `validado_github` — repositório verificado em github.com
  - `validado_doc_oficial` — página oficial AMD/PyTorch/ROCm/Taichi
  - `fonte_primaria_inacessivel` — só disponível em domínio fora da allowlist (IEEE, ACM, etc.) — **não citar até revalidar manualmente**
  - `incerto` — paper recente ou metadado não confirmado em fonte primária

> **Observação metodológica do orientador:** este fichamento é um *mapa de leitura*, **não substitui a leitura dos papers**. Antes de citar qualquer item no Cap. 2-5, leia o paper. A `ideia_chave` aqui é um lembrete, não dispensa a leitura primária. Não invente número de página, equação ou figura — abra o PDF e confira.

## Convenção de citação ABNT

- **Citação no corpo (autor-data, NBR 10520):**
  - 1 autor: `(MILDENHALL, 2020)` ou `Mildenhall (2020)`
  - 2-3 autores: `(BARRON; MILDENHALL; TANCIK, 2021)`
  - 4+ autores: `(MILDENHALL et al., 2020)`
- **Referência (NBR 6023):**
  - Sobrenome em CAIXA ALTA, demais nomes seguindo. Título em itálico (ou negrito, escolha um padrão e mantenha). Edição, local, editora, ano.
  - Para artigos arXiv: incluir `Disponível em: <URL>. Acesso em: AAAA-MM-DD.`
- **Padrão deste TCC:** sobrenome do primeiro autor MAIÚSCULO + et al. quando 4+; ano sempre o ano de publicação no venue (não o do preprint).

---

## Eixo A — Fundamentos de Renderização Neural

### A.1 — Mildenhall et al. (2020) — NeRF [validado_arxiv]
- **Autores:** Ben Mildenhall, Pratul P. Srinivasan, Matthew Tancik, Jonathan T. Barron, Ravi Ramamoorthi, Ren Ng
- **Título:** NeRF: Representing Scenes as Neural Radiance Fields for View Synthesis
- **Venue:** ECCV 2020 (oral)
- **arXiv:** [2003.08934](https://arxiv.org/abs/2003.08934)
- **Ideia-chave:** Representa uma cena como um MLP que mapeia coordenada 5D (posição 3D + direção 2D) → densidade volumétrica + cor view-dependent, otimizado por volume rendering diferenciável treinado apenas com imagens posadas.
- **Relevância TCC:** Paper-base de toda a família de campos de radiância neurais. Qualquer experimento de portabilidade parte da formulação canônica deste artigo. Também introduz o dataset **Synthetic-NeRF** (8 cenas Blender) usado em quase todos os benchmarks subsequentes.
- **Onde citar:** Cap. 2 (definição formal de NeRF e volume rendering); Cap. 4 (datasets).

### A.2 — Park et al. (2019) — DeepSDF [validado_arxiv]
- **Autores:** Jeong Joon Park, Peter Florence, Julian Straub, Richard Newcombe, Steven Lovegrove
- **Título:** DeepSDF: Learning Continuous Signed Distance Functions for Shape Representation
- **Venue:** CVPR 2019
- **arXiv:** [1901.05103](https://arxiv.org/abs/1901.05103)
- **Ideia-chave:** Aprende SDF contínua via rede profunda capaz de codificar uma classe inteira de formas 3D, com a superfície representada implicitamente como o zero-level-set.
- **Relevância TCC:** Fundamenta a vertente de representações implícitas baseadas em SDF (alternativa a NeRF), com pipelines de marching e ray-tracing diferentes — relevante para discutir cargas de trabalho heterogêneas em GPU.
- **Onde citar:** Cap. 2 (representações implícitas: SDF neural).

### A.3 — Mescheder et al. (2019) — Occupancy Networks [validado_arxiv]
- **Autores:** Lars Mescheder, Michael Oechsle, Michael Niemeyer, Sebastian Nowozin, Andreas Geiger
- **Título:** Occupancy Networks: Learning 3D Reconstruction in Function Space
- **Venue:** CVPR 2019
- **arXiv:** [1812.03828](https://arxiv.org/abs/1812.03828)
- **Ideia-chave:** Representa a superfície 3D implicitamente como a fronteira de decisão contínua de um classificador neural de ocupação, permitindo resolução arbitrária sem custo de memória de voxel grid.
- **Relevância TCC:** Junto com DeepSDF, define a família "implicit function networks" que motivou as escolhas arquiteturais do NeRF e estabelece o trade-off entre representação implícita versus explícita.
- **Onde citar:** Cap. 2 (representações implícitas: redes de ocupação).

### A.4 — Sitzmann; Zollhöfer; Wetzstein (2019) — SRN [validado_arxiv]
- **Autores:** Vincent Sitzmann, Michael Zollhöfer, Gordon Wetzstein
- **Título:** Scene Representation Networks: Continuous 3D-Structure-Aware Neural Scene Representations
- **Venue:** NeurIPS 2019
- **arXiv:** [1906.01618](https://arxiv.org/abs/1906.01618)
- **Ideia-chave:** Função contínua que mapeia coordenadas mundiais para descritores locais, treinada via ray-marching diferenciável usando apenas imagens 2D e poses, antecipando ideias-chave do NeRF.
- **Relevância TCC:** Antecedente direto do NeRF. Útil para a narrativa histórica e para mostrar que o ray-marching diferenciável (carga de trabalho central no experimento) precede o NeRF.
- **Onde citar:** Cap. 2 (histórico de representações neurais 3D).

### A.5 — Wang et al. (2021) — NeuS [validado_arxiv]
- **Autores:** Peng Wang, Lingjie Liu, Yuan Liu, Christian Theobalt, Taku Komura, Wenping Wang
- **Título:** NeuS: Learning Neural Implicit Surfaces by Volume Rendering for Multi-view Reconstruction
- **Venue:** NeurIPS 2021
- **arXiv:** [2106.10689](https://arxiv.org/abs/2106.10689)
- **Ideia-chave:** Combina SDF neural com volume rendering estilo NeRF, propondo formulação livre de viés em primeira ordem para reconstrução de superfícies de alta qualidade sem máscaras.
- **Relevância TCC:** Híbrido NeRF+SDF que ilustra a fusão das duas grandes famílias implícitas. Útil para discutir variantes que mudam o perfil de carga computacional sobre a GPU.
- **Onde citar:** Cap. 2 (representações híbridas SDF/volume).

### A.6 — Kerbl et al. (2023) — 3D Gaussian Splatting [validado_arxiv]
- **Autores:** Bernhard Kerbl, Georgios Kopanas, Thomas Leimkühler, George Drettakis
- **Título:** 3D Gaussian Splatting for Real-Time Radiance Field Rendering
- **Venue:** ACM Transactions on Graphics, vol. 42, n. 4 (SIGGRAPH 2023)
- **arXiv:** [2308.04079](https://arxiv.org/abs/2308.04079)
- **Ideia-chave:** Representa cena explicitamente como milhões de gaussianas anisotrópicas otimizadas, renderizadas por rasterização diferenciável visibility-aware, atingindo ≥30 fps a 1080p com qualidade SOTA.
- **Relevância TCC:** Paper central para a parte de representação explícita. O pipeline de rasterização gaussiana é exatamente uma das cargas que se quer portar para RDNA 4 via ROCm/HIP/Vulkan. Implementação oficial é CUDA + PyTorch (rasterizador customizado, **não** tiny-cuda-nn).
- **Onde citar:** Cap. 2 (3DGS — fundamentos); Cap. 4 (alvo do experimento).

### A.7 — Müller et al. (2022) — Instant-NGP [validado_arxiv]
- **Autores:** Thomas Müller, Alex Evans, Christoph Schied, Alexander Keller
- **Título:** Instant Neural Graphics Primitives with a Multiresolution Hash Encoding
- **Venue:** ACM Transactions on Graphics, vol. 41, n. 4, art. 102 (SIGGRAPH 2022)
- **arXiv:** [2201.05989](https://arxiv.org/abs/2201.05989)
- **Ideia-chave:** Hash encoding multirresolução com tabela de features treinável + MLP pequeno via kernels CUDA fully-fused (tiny-cuda-nn). Treina NeRF em segundos.
- **Relevância TCC:** Caso paradigmático do acoplamento NeRF↔CUDA. Implementação oficial usa tiny-cuda-nn + Tensor Cores. Alvo central do experimento de portabilidade.
- **Onde citar:** Cap. 2 (NeRF acelerado); Cap. 3 (ecossistema CUDA); Cap. 4 (alvo do experimento).

### A.8 — Zhang et al. (2018) — LPIPS [validado_arxiv]
- **Autores:** Richard Zhang, Phillip Isola, Alexei A. Efros, Eli Shechtman, Oliver Wang
- **Título:** The Unreasonable Effectiveness of Deep Features as a Perceptual Metric
- **Venue:** CVPR 2018
- **arXiv:** [1801.03924](https://arxiv.org/abs/1801.03924)
- **Ideia-chave:** Demonstra que features de redes profundas (LPIPS) capturam similaridade perceptual humana melhor que PSNR/SSIM, propondo uma métrica perceptual padronizada.
- **Relevância TCC:** Define LPIPS, métrica obrigatória junto com PSNR/SSIM em qualquer benchmark de NeRF/3DGS. Base para comparar fidelidade entre backends CUDA, ROCm, Vulkan e Taichi.
- **Onde citar:** Cap. 4 (metodologia experimental: métricas de qualidade).

### A.9 — Tewari et al. (2020) — State of the Art on Neural Rendering (STAR) [validado_arxiv]
- **Autores:** Ayush Tewari, Ohad Fried, Justus Thies, Vincent Sitzmann, Stephen Lombardi, Kalyan Sunkavalli, Ricardo Martin-Brualla, Tomas Simon, Jason Saragih, Matthias Nießner, Rohit Pandey, Sean Fanello, Gordon Wetzstein, Jun-Yan Zhu, Christian Theobalt, Maneesh Agrawala, Eli Shechtman, Dan B Goldman, Michael Zollhöfer
- **Título:** State of the Art on Neural Rendering
- **Venue:** Eurographics 2020 — STAR (State of the Art Report)
- **arXiv:** [2004.03805](https://arxiv.org/abs/2004.03805)
- **Ideia-chave:** Survey fundador do campo: organiza taxonomia de neural rendering combinando CG clássico com modelos generativos, cobrindo síntese de novas vistas, manipulação semântica e relighting.
- **Relevância TCC:** Survey de referência para introduzir o campo na revisão bibliográfica. Útil para situar o leitor antes de mergulhar em NeRF/3DGS.
- **Onde citar:** Cap. 2 (introdução à renderização neural).

### A.10 — Tewari et al. (2022) — Advances in Neural Rendering [validado_arxiv]
- **Autores:** Ayush Tewari, Justus Thies, Ben Mildenhall, Pratul Srinivasan, Edgar Tretschk, Yifan Wang, Christoph Lassner, Vincent Sitzmann, Ricardo Martin-Brualla, Stephen Lombardi, Tomas Simon, Christian Theobalt, Matthias Nießner, Jonathan T. Barron, Gordon Wetzstein, Michael Zollhoefer, Vladislav Golyanik
- **Título:** Advances in Neural Rendering
- **Venue:** Eurographics 2022 — STAR
- **arXiv:** [2111.05849](https://arxiv.org/abs/2111.05849)
- **Ideia-chave:** Continuação do STAR de 2020, focada em representações de cena 3D-consistentes (NeRF e variantes), cobrindo cenas estáticas e deformações não-rígidas.
- **Relevância TCC:** Survey mais atualizado para situar a explosão pós-NeRF. Complementa Tewari 2020 e cobre o gap até a chegada do 3DGS.
- **Onde citar:** Cap. 2 (estado da arte pós-NeRF).

### A.11 — Chen; Wang (2024) — Survey on 3DGS [validado_arxiv]
- **Autores:** Guikun Chen, Wenguan Wang
- **Título:** A Survey on 3D Gaussian Splatting
- **Venue:** ACM Computing Surveys (preprint arXiv 2024)
- **arXiv:** [2401.03890](https://arxiv.org/abs/2401.03890)
- **Ideia-chave:** Primeiro survey sistemático sobre 3DGS, cobrindo princípios, variantes, aplicações em VR/mídia e benchmarks comparativos.
- **Relevância TCC:** Mapa essencial para escolher os derivados de 3DGS a benchmarcar no experimento (compactos, dinâmicos, edição) e identificar as implementações de referência.
- **Onde citar:** Cap. 2 (panorama 3DGS); Cap. 4 (seleção de baselines).

### A.12 — Wang et al. (2004) — SSIM [fonte_primaria_inacessivel]
- **Autores:** Zhou Wang, Alan C. Bovik, Hamid R. Sheikh, Eero P. Simoncelli
- **Título:** Image Quality Assessment: From Error Visibility to Structural Similarity
- **Venue:** IEEE Transactions on Image Processing, vol. 13, n. 4, p. 600-612, 2004
- **DOI:** 10.1109/TIP.2003.819861 (a confirmar manualmente)
- **Ideia-chave:** Propõe SSIM, métrica baseada em luminância, contraste e estrutura local, alinhada com percepção humana e superior ao MSE/PSNR para julgamento de fidelidade.
- **Relevância TCC:** Métrica canônica para reportar qualidade visual em todo benchmark de NeRF/3DGS.
- **Onde citar:** Cap. 4 (métricas de qualidade).
- **Pendência:** publicado em IEEE Xplore (sem preprint arXiv). Baixar via biblioteca da UFC e confirmar paginação antes do depósito.

### A.13 — Kajiya; Von Herzen (1984) — Volume Rendering clássico [fonte_primaria_inacessivel]
- **Autores:** James T. Kajiya, Brian P. Von Herzen
- **Título:** Ray Tracing Volume Densities
- **Venue:** Computer Graphics (Proc. SIGGRAPH '84), vol. 18, n. 3, p. 165-174
- **DOI:** 10.1145/964965.808594 (a confirmar)
- **Ideia-chave:** Formaliza a equação de transporte de radiância em meios participantes e o algoritmo de ray-tracing volumétrico — base matemática da renderização volumétrica diferenciável usada em NeRF.
- **Relevância TCC:** Origem da equação de volume rendering compositada que NeRF discretiza.
- **Onde citar:** Cap. 2 (fundamentos de volume rendering pré-deep learning).
- **Pendência:** ACM Digital Library (fora da allowlist). Sem preprint arXiv (1984). Confirmar paginação manualmente.

### A.14 — Westover (1990) — Splatting clássico [fonte_primaria_inacessivel]
- **Autores:** Lee Westover
- **Título:** Footprint Evaluation for Volume Rendering
- **Venue:** Computer Graphics (Proc. SIGGRAPH '90), vol. 24, n. 4, p. 367-376
- **Ideia-chave:** Introduz o algoritmo de splatting (footprint evaluation) para rendering volumétrico — projeta cada voxel como kernel 2D no plano de imagem, antecedente direto do 3DGS.
- **Relevância TCC:** Origem histórica do splatting. Ponte conceitual obrigatória entre o CG clássico e o 3DGS.
- **Onde citar:** Cap. 2 (origem do splatting).
- **Pendência:** ACM DL fora da allowlist; sem preprint. Confirmar manualmente.

---

## Eixo B — Otimizações e Variantes de Renderização Neural

### B.1 — Yu et al. (2022) — Plenoxels [validado_arxiv]
- **Autores:** Alex Yu, Sara Fridovich-Keil, Matthew Tancik, Qinhong Chen, Benjamin Recht, Angjoo Kanazawa
- **Título:** Plenoxels: Radiance Fields without Neural Networks
- **Venue:** CVPR 2022 (preprint dez/2021)
- **arXiv:** [2112.05131](https://arxiv.org/abs/2112.05131)
- **Ideia-chave:** Grade esparsa de voxels com harmônicos esféricos, **sem rede neural**, otimizada por gradiente. Duas ordens de grandeza mais rápida que NeRF.
- **Relevância TCC:** Não depende de Tensor Cores nem de tiny-cuda-nn → bom candidato a port direto via Vulkan/Taichi e baseline para discutir o que é "neural" na renderização neural. (Atenção: primeiro autor é Alex Yu, não Fridovich-Keil — convenção ABNT usa o primeiro.)
- **Onde citar:** Cap. 3 (NeRF acelerado / representações sem MLP).

### B.2 — Sun; Sun; Chen (2022) — DVGO [validado_arxiv]
- **Autores:** Cheng Sun, Min Sun, Hwann-Tzong Chen
- **Título:** Direct Voxel Grid Optimization: Super-fast Convergence for Radiance Fields Reconstruction
- **Venue:** CVPR 2022
- **arXiv:** [2111.11215](https://arxiv.org/abs/2111.11215)
- **Ideia-chave:** Grades de voxels separadas para densidade e features (com MLP raso), com pós-ativação interpolada; converge em < 15 min em uma GPU.
- **Relevância TCC:** Família "voxel grid + MLP raso" — grosso do custo em operações de grade (mais portáveis), pouco em MLP. Bom para benchmark cross-vendor.
- **Onde citar:** Cap. 3 (NeRF acelerado).

### B.3 — Chen et al. (2022) — TensoRF [validado_arxiv]
- **Autores:** Anpei Chen, Zexiang Xu, Andreas Geiger, Jingyi Yu, Hao Su
- **Título:** TensoRF: Tensorial Radiance Fields
- **Venue:** ECCV 2022
- **arXiv:** [2203.09517](https://arxiv.org/abs/2203.09517)
- **Ideia-chave:** Representa o campo de radiância como tensor 4D decomposto (CP ou Vector-Matrix), reduzindo memória e tempo de treino.
- **Relevância TCC:** Decomposição tensorial implementável em qualquer backend de álgebra linear. Bom para discutir portabilidade sem dependência de kernels especializados em CUDA.
- **Onde citar:** Cap. 3 (NeRF acelerado / representações compactas).

### B.4 — Barron et al. (2021) — Mip-NeRF [validado_arxiv]
- **Autores:** Jonathan T. Barron, Ben Mildenhall, Matthew Tancik, Peter Hedman, Ricardo Martin-Brualla, Pratul P. Srinivasan
- **Título:** Mip-NeRF: A Multiscale Representation for Anti-Aliasing Neural Radiance Fields
- **Venue:** ICCV 2021
- **arXiv:** [2103.13415](https://arxiv.org/abs/2103.13415)
- **Ideia-chave:** Integra cones (frustums) em vez de raios para representar escala continuamente, eliminando aliasing em multi-resolução.
- **Relevância TCC:** Referência sobre qualidade. Útil para discutir *quality vs throughput* em diferentes hardwares.
- **Onde citar:** Cap. 3 (anti-aliasing / extensões de NeRF).

### B.5 — Barron et al. (2022) — Mip-NeRF 360 [validado_arxiv]
- **Autores:** Jonathan T. Barron, Ben Mildenhall, Dor Verbin, Pratul P. Srinivasan, Peter Hedman
- **Título:** Mip-NeRF 360: Unbounded Anti-Aliased Neural Radiance Fields
- **Venue:** CVPR 2022
- **arXiv:** [2111.12077](https://arxiv.org/abs/2111.12077)
- **Ideia-chave:** Estende Mip-NeRF para cenas 360° não-limitadas com parametrização não-linear, destilação online e regularização de distorção.
- **Relevância TCC:** Introduz o **Mip-NeRF 360 dataset** — benchmark canônico para 3DGS/Zip-NeRF/Nerfacto. Dataset central previsto para o experimento.
- **Onde citar:** Cap. 3 (extensões de NeRF); Cap. 4 (datasets).

### B.6 — Barron et al. (2023) — Zip-NeRF [validado_arxiv]
- **Autores:** Jonathan T. Barron, Ben Mildenhall, Dor Verbin, Pratul P. Srinivasan, Peter Hedman
- **Título:** Zip-NeRF: Anti-Aliased Grid-Based Neural Radiance Fields
- **Venue:** ICCV 2023
- **arXiv:** [2304.06706](https://arxiv.org/abs/2304.06706)
- **Ideia-chave:** Combina raciocínio sub-volumétrico de Mip-NeRF 360 com hash grids tipo Instant-NGP — anti-aliasing + aceleração por grade.
- **Relevância TCC:** Estado da arte em qualidade NeRF. Herda dependência prática de tiny-cuda-nn na implementação de referência. Bom alvo aspiracional do experimento.
- **Onde citar:** Cap. 3 (state-of-the-art NeRF).

### B.7 — Lin et al. (2021) — BARF [validado_arxiv]
- **Autores:** Chen-Hsuan Lin, Wei-Chiu Ma, Antonio Torralba, Simon Lucey
- **Título:** BARF: Bundle-Adjusting Neural Radiance Fields
- **Venue:** ICCV 2021 (oral)
- **arXiv:** [2104.06405](https://arxiv.org/abs/2104.06405)
- **Ideia-chave:** Otimiza conjuntamente representação NeRF e poses de câmera por registro coarse-to-fine no encoding posicional.
- **Relevância TCC:** Robustez prática com captura "in-the-wild" — pertinente caso o experimento use dados próprios sem COLMAP perfeito.
- **Onde citar:** Cap. 3 (refinamento de poses); Cap. 4 (metodologia, opcional).

### B.8 — Yang et al. (2024) — Deformable 3DGS [validado_arxiv]
- **Autores:** Ziyi Yang, Xinyu Gao, Wen Zhou, Shaohui Jiao, Yuqing Zhang, Xiaogang Jin
- **Título:** Deformable 3D Gaussians for High-Fidelity Monocular Dynamic Scene Reconstruction
- **Venue:** CVPR 2024 (preprint set/2023)
- **arXiv:** [2309.13101](https://arxiv.org/abs/2309.13101)
- **Ideia-chave:** Gaussianas em espaço canônico + campo de deformação para cenas dinâmicas monoculares, com mecanismo de annealing.
- **Relevância TCC:** Fronteira "dinâmica" do 3DGS. Útil para delimitar escopo do TCC (focar em estáticas) e contextualizar o ecossistema.
- **Onde citar:** Cap. 3 (variantes 3DGS — dinâmico).

### B.9 — Wu et al. (2024) — 4D Gaussian Splatting [validado_arxiv]
- **Autores:** Guanjun Wu, Taoran Yi, Jiemin Fang, Lingxi Xie, Xiaopeng Zhang, Wei Wei, Wenyu Liu, Qi Tian, Xinggang Wang
- **Título:** 4D Gaussian Splatting for Real-Time Dynamic Scene Rendering
- **Venue:** CVPR 2024
- **arXiv:** [2310.08528](https://arxiv.org/abs/2310.08528)
- **Ideia-chave:** Representação 4D unificada (gaussianas 3D + voxels neurais 4D decompostos tipo HexPlane) com MLP leve prevendo deformações por timestamp; 82 FPS @ 800x800 em RTX 3090.
- **Relevância TCC:** Cita FPS em hardware NVIDIA específico → bom alvo de comparação cross-vendor (RTX 3090 vs RX 9070 XT) caso o experimento aborde 4D.
- **Onde citar:** Cap. 3 (variantes 3DGS — dinâmico).

### B.10 — Lu et al. (2024) — Scaffold-GS [validado_arxiv]
- **Autores:** Tao Lu, Mulin Yu, Linning Xu, Yuanbo Xiangli, Limin Wang, Dahua Lin, Bo Dai
- **Título:** Scaffold-GS: Structured 3D Gaussians for View-Adaptive Rendering
- **Venue:** CVPR 2024 (preprint nov/2023)
- **arXiv:** [2312.00109](https://arxiv.org/abs/2312.00109)
- **Ideia-chave:** Pontos-âncora estruturam gaussianas locais cujos atributos são preditos on-the-fly por direção/distância de visualização.
- **Relevância TCC:** Tendência "structured Gaussians". Importante para discussão de eficiência de memória, relevante em GPUs com VRAM diferente da RTX 4090.
- **Onde citar:** Cap. 3 (variantes 3DGS — eficiência/estrutura).

### B.11 — Cheng et al. (2024) — GaussianPro [validado_arxiv]
- **Autores:** Kai Cheng, Xiaoxiao Long, Kaizhi Yang, Yao Yao, Wei Yin, Yuexin Ma, Wenping Wang, Xuejin Chen
- **Título:** GaussianPro: 3D Gaussian Splatting with Progressive Propagation
- **Venue:** ICML 2024 (a confirmar)
- **arXiv:** [2402.14650](https://arxiv.org/abs/2402.14650)
- **Ideia-chave:** Propagação progressiva inspirada em MVS clássico para densificar gaussianas em cenas grandes/sem textura, contornando inicialização SfM esparsa; +1.15 dB PSNR no Waymo.
- **Relevância TCC:** Inicialização — gargalo prático em cenas reais. Relevante se o experimento envolver cenas próprias com COLMAP fraco.
- **Onde citar:** Cap. 3 (variantes 3DGS — qualidade de inicialização).

### B.12 — Tancik et al. (2023) — Nerfstudio [validado_arxiv]
- **Autores:** Matthew Tancik, Ethan Weber, Evonne Ng, Ruilong Li, Brent Yi, Justin Kerr, Terrance Wang, Alexander Kristoffersen, Jake Austin, Kamyar Salahi, Abhik Ahuja, David McAllister, Angjoo Kanazawa
- **Título:** Nerfstudio: A Modular Framework for Neural Radiance Field Development
- **Venue:** SIGGRAPH 2023
- **arXiv:** [2302.04264](https://arxiv.org/abs/2302.04264)
- **Ideia-chave:** Framework modular em PyTorch que organiza componentes de NeRF (data, modelos, viewer, exportadores). Inclui o método "Nerfacto".
- **Relevância TCC:** Provável base operacional do experimento — Nerfstudio + nerfacto + gsplat permitem rodar NeRF e 3DGS num pipeline unificado, e a portabilidade para AMD se dá no nível PyTorch ROCm.
- **Onde citar:** Cap. 3 (frameworks); Cap. 4 (pipeline experimental).

### B.13 — NVlabs (2022) — tiny-cuda-nn [validado_github]
- **Autores/mantenedor:** Thomas Müller (NVlabs) e contribuidores
- **Título:** tiny-cuda-nn — Lightning fast C++/CUDA neural network framework
- **Venue:** Projeto open source (sem paper próprio; descrito em Müller et al. 2022)
- **URL:** [github.com/NVlabs/tiny-cuda-nn](https://github.com/NVlabs/tiny-cuda-nn)
- **Ideia-chave:** MLP "fully-fused" em CUDA + multiresolution hash encoding; alvo de Tensor Cores; binding PyTorch.
- **Relevância TCC:** **ELEMENTO CENTRAL DA TESE de portabilidade.** Exemplo canônico de dependência *hard* CUDA/Tensor Cores no ecossistema NeRF — Instant-NGP, partes do Nerfstudio e Zip-NeRF dependem dele.
- **Onde citar:** Cap. 2 (motivação); Cap. 3 (dependências CUDA); Cap. 5 (discussão de portabilidade).

### B.14 — nerfstudio-project (2023) — gsplat [validado_github]
- **Autores/mantenedor:** Equipe nerfstudio-project (Apache-2.0)
- **Título:** gsplat — CUDA-accelerated rasterization of Gaussian Splatting
- **Venue:** Projeto open source com paper companion (Ye et al.; não validado nesta rodada)
- **URL:** [github.com/nerfstudio-project/gsplat](https://github.com/nerfstudio-project/gsplat)
- **Ideia-chave:** Rasterizador 3DGS em CUDA com bindings PyTorch, integrável ao Nerfstudio; reescrita do rasterizador original com foco em performance, memória e features.
- **Relevância TCC:** Implementação alternativa ao código INRIA — também CUDA, mas mais limpo e modular, melhor candidato a porting para HIP. Forte alvo experimental.
- **Onde citar:** Cap. 3 (stack 3DGS); Cap. 4 (pipeline experimental).

---

## Eixo C — Hardware, Paralelismo e Portabilidade

### C.1 — Hu et al. (2019) — Taichi [validado_github]
- **Autores:** Yuanming Hu, Tzu-Mao Li, Luke Anderson, Jonathan Ragan-Kelley, Frédo Durand
- **Título:** Taichi: a language for high-performance computation on spatially sparse data structures
- **Venue:** ACM Transactions on Graphics 38(6), Art. 201 — SIGGRAPH Asia 2019
- **URL primária:** PDF do autor (yuanming.taichi.graphics) — BibTeX confirmado em [taichi-dev/taichi BibTeX](https://raw.githubusercontent.com/taichi-dev/taichi/master/misc/taichi_bibtex.txt)
- **Ideia-chave:** DSL embutida em C++/Python para computação de alto desempenho sobre estruturas de dados esparsas, com decoupling explícito entre algoritmo e layout de memória, gerando código paralelo para múltiplos backends.
- **Relevância TCC:** Fundamento teórico do principal "veículo de portabilidade" do TCC. Justifica a escolha de Taichi como abordagem write-once-run-anywhere para experimentos na RX 9070 XT.
- **Onde citar:** Cap. 3 (linguagens e DSLs para GPU); Cap. 4 (metodologia experimental).

### C.2 — Hu et al. (2020) — DiffTaichi [validado_arxiv]
- **Autores:** Yuanming Hu, Luke Anderson, Tzu-Mao Li, Qi Sun, Nathan Carr, Jonathan Ragan-Kelley, Frédo Durand
- **Título:** DiffTaichi: Differentiable Programming for Physical Simulation
- **Venue:** ICLR 2020
- **arXiv:** [1910.00935](https://arxiv.org/abs/1910.00935)
- **Ideia-chave:** Estende Taichi com diferenciação automática por transformação de código-fonte, mantendo intensidade aritmética e paralelismo. Mostra que simulador elástico em DiffTaichi tem 4,2x menos código que CUDA hand-written com desempenho equivalente.
- **Relevância TCC:** Demonstra que portabilidade (Taichi) não implica abdicar de diferenciabilidade — crítico para renderização neural treinável em hardware não-CUDA.
- **Onde citar:** Cap. 3 (linguagens diferenciáveis para GPU).

### C.3 — taichi-dev (2025) — Repositório Taichi [validado_github]
- **Autores:** Comunidade Taichi Lang (taichi-dev)
- **Título:** taichi: Productive, portable, and performant GPU programming in Python
- **Venue:** Repositório GitHub (release v1.7.4, jul/2025)
- **URL:** [github.com/taichi-dev/taichi](https://github.com/taichi-dev/taichi)
- **Ideia-chave:** Implementação de referência da linguagem Taichi. Backends estáveis: CPU x64/ARM, CUDA, Vulkan, OpenGL 4.3+, Metal e WebAssembly (experimental). Backend AMDGPU presente mas considerado experimental — fixes recentes (v1.7.4, PR #8667) tratam compatibilidade com ROCm 6.x.
- **Relevância TCC:** Define o estado real do suporte multi-backend de Taichi. Backend Vulkan é a rota mais portátil para RX 9070 XT; AMDGPU/ROCm via Taichi é vetor experimental que o TCC pode documentar.
- **Onde citar:** Cap. 4 (metodologia); Cap. 5 (discussão).

### C.4 — Linyou (2023) — taichi-ngp-renderer [validado_github]
- **Autores/mantenedor:** Linyou
- **Título:** taichi-ngp-renderer: Instant-NGP renderer implemented in Taichi (No CUDA)
- **Venue:** Repositório GitHub
- **URL:** [github.com/Linyou/taichi-ngp-renderer](https://github.com/Linyou/taichi-ngp-renderer)
- **Ideia-chave:** Porte do estágio de inferência/rendering do Instant-NGP escrito 100% em Python+Taichi (sem CUDA). Implementa hash encoding, MLP fundido em shared memory, ray marching e volume rendering — ~66 fps a 800x800 numa RTX 3090. Faz workarounds explícitos pela ausência de TensorCore via Taichi.
- **Relevância TCC:** **Prova de conceito direta** de NeRF/Instant-NGP fora do CUDA. Referência de baseline e ponto de partida para o experimento na RX 9070 XT (basta trocar backend para Vulkan).
- **Onde citar:** Cap. 4 (metodologia); Cap. 5 (resultados).

### C.5 — Taichi Lang (2023) — Documentação oficial backends [validado_doc_oficial]
- **Autores:** Taichi Lang Documentation Team
- **Título:** Taichi Documentation — Hello World / Backends
- **Venue:** Documentação oficial v1.6.0 (consulta 2026-06)
- **URL:** [docs.taichi-lang.org/docs/hello_world](https://docs.taichi-lang.org/docs/hello_world)
- **Ideia-chave:** Matriz oficial de plataformas suportadas: CPU em todas; CUDA em Win/Linux; OpenGL em Win/Linux; Metal só macOS; Vulkan em Win/Linux/macOS. AMDGPU **não aparece** na matriz pública desta versão (apesar de existir no código), sinalizando maturidade desigual.
- **Relevância TCC:** Documenta de forma primária a "lacuna" no suporte AMD oficial em Taichi — ponto central do TCC sobre portabilidade prática vs. portabilidade prometida.
- **Onde citar:** Cap. 3 (panorama de backends); Cap. 4 (escolha do pipeline experimental).

### C.6 — Markidis et al. (2018) — NVIDIA Tensor Core Programmability [validado_arxiv]
- **Autores:** Stefano Markidis, Steven Wei Der Chien, Erwin Laure, Ivy Bo Peng, Jeffrey S. Vetter
- **Título:** NVIDIA Tensor Core Programmability, Performance & Precision
- **Venue:** IPDPS Workshops 2018 (AsHES); IEEE DOI 10.1109/IPDPSW.2018.00091
- **arXiv:** [1803.04014](https://arxiv.org/abs/1803.04014)
- **Ideia-chave:** Primeira caracterização acadêmica dos Tensor Cores (Volta V100). Compara WMMA, CUTLASS e cuBLAS GEMM, atingindo até 83 Tflops/s mixed-precision (~7x sobre FP32).
- **Relevância TCC:** Estabelece o ponto de partida histórico do "monopólio CUDA via Tensor Cores" que o TCC contrasta. Necessário para justificar por que Tensor Cores viraram diferencial competitivo.
- **Onde citar:** Cap. 3 (arquitetura de aceleradores matriciais); Cap. 5 (discussão).

### C.7 — Sun et al. (2022) — Dissecting Tensor Cores via Microbenchmarks [validado_arxiv]
- **Autores:** Wei Sun, Ang Li, Tong Geng, Sander Stuijk, Henk Corporaal
- **Título:** Dissecting Tensor Cores via Microbenchmarks: Latency, Throughput and Numeric Behaviors
- **Venue:** IEEE TPDS 2022 — DOI 10.1109/TPDS.2022.3217824
- **arXiv:** [2206.02874](https://arxiv.org/abs/2206.02874)
- **Ideia-chave:** Atualização e extensão de "Demystifying Tensor Cores" para Ampere, comparando APIs wmma vs mma e caracterizando comportamento numérico de TF32, BF16 e FP16. Inclui sparsity em Ampere.
- **Relevância TCC:** Referência atual e validada para caracterizar Tensor Cores em geração 2020+. Útil para justificar por que software portátil sofre se não toca essa hierarquia de instruções.
- **Onde citar:** Cap. 3 (aceleradores matriciais); Cap. 5 (gaps NVIDIA vs AMD).

### C.8 — Abdelkhalik et al. (2022) — Ampere Microbenchmark [validado_arxiv]
- **Autores:** Hamdy Abdelkhalik, Yehia Arafa, Nandakishore Santhi, Abdel-Hameed Badawy
- **Título:** Demystifying the Nvidia Ampere Architecture through Microbenchmarking and Instruction-level Analysis
- **Venue:** arXiv preprint (cs.AR), 2022
- **arXiv:** [2208.11174](https://arxiv.org/abs/2208.11174)
- **Ideia-chave:** Microbenchmarks de PTX/SASS na Ampere — latências por instrução, hierarquia de memória e Tensor Cores via WMMA em diferentes shapes/tipos.
- **Relevância TCC:** Números de referência da geração imediatamente anterior à Hopper/Blackwell. Útil para fixar baseline NVIDIA.
- **Onde citar:** Cap. 3 (microarquitetura de GPUs).

### C.9 — Luo et al. (2024) — Hopper Architecture Benchmarking [validado_arxiv]
- **Autores:** Weile Luo, Ruibo Fan, Zeyu Li, Dayou Du, Qiang Wang, Xiaowen Chu
- **Título:** Benchmarking and Dissecting the Nvidia Hopper GPU Architecture
- **Venue:** arXiv preprint (cs.AR), 2024
- **arXiv:** [2402.13499](https://arxiv.org/abs/2402.13499)
- **Ideia-chave:** Microbenchmarks de Hopper (H100), focando FP8 Tensor Cores, instruções DPX, distributed shared memory. Compara contra Ada e Ampere.
- **Relevância TCC:** Caracterização atualizada da geração de elite NVIDIA (datacenter), permitindo contrastar com CDNA 3 (MI300) e RDNA 4 (RX 9070 XT) sem extrapolar de marketing.
- **Onde citar:** Cap. 3 (microarquitetura).

### C.10 — Xie et al. (2025) — Bit-Accurate MMA Modeling [validado_arxiv, **paper recente — revalidar**]
- **Autores:** Peichen Xie, Shuotao Xu, Yang Wang, Fan Yang, Mao Yang
- **Título:** Bit-Accurate Modeling of GPU Matrix Multiply-Accumulate Units: Demystifying Numerical Discrepancy and Accuracy
- **Venue:** arXiv preprint (cs.AR / cs.LG), 2025
- **arXiv:** [2511.10909](https://arxiv.org/abs/2511.10909)
- **Ideia-chave:** Constrói modelos bit-accurate de unidades MMA cobrindo 10 arquiteturas — Volta a Blackwell (NVIDIA) e CDNA1 a CDNA3 (AMD). Identifica gargalos de precisão e **assimetria numérica entre vendors**. Código aberto em microsoft/MMA-Sim.
- **Relevância TCC:** Referência de ponta para o que o TCC quer discutir: por que a mesma operação pode dar resultados diferentes em hardware NVIDIA vs AMD, com impacto em treinamento neural.
- **Onde citar:** Cap. 5 (precisão e reprodutibilidade).
- **Atenção:** Paper recente — verificar arXiv pessoalmente antes de citar.

### C.11 — AMD (2025) — ROCm Documentation [validado_doc_oficial]
- **Autor:** Advanced Micro Devices, Inc.
- **Título:** ROCm Documentation — System Requirements / Supported GPUs
- **Venue:** Documentação oficial ROCm 7.2.4 (production); 7.13.0 (preview)
- **URL:** [rocm.docs.amd.com/projects/install-on-linux/.../system-requirements.html](https://rocm.docs.amd.com/projects/install-on-linux/en/latest/reference/system-requirements.html)
- **Ideia-chave:** Matriz oficial de GPUs suportadas. RDNA 4 (gfx1200/gfx1201, **incluindo RX 9070 XT**, 9070, 9060 XT, 9060 e variantes Radeon AI PRO) entrou na lista de "Supported", restritos a Ubuntu 22.04.5 / 24.04.4 e RHEL 9.7 / 10.1. CDNA 4 (gfx950, MI355X/MI350X) também listado.
- **Relevância TCC:** **FONTE PRIMÁRIA INDISPENSÁVEL** — confirma que a RX 9070 XT É oficialmente suportada por ROCm 7.x, contrariando o histórico de exclusão de Radeon de consumo. Documentar versão consultada e SO escolhido.
- **Onde citar:** Cap. 2 (estado da arte); Cap. 4 (setup experimental).

### C.12 — AMD (2025) — HIP Programming Model [validado_doc_oficial]
- **Autor:** Advanced Micro Devices, Inc.
- **Título:** HIP Programming Guide — Programming Model
- **Venue:** Documentação oficial HIP 7.2.x (parte do ROCm 7.2.4)
- **URL:** [rocm.docs.amd.com/projects/HIP/.../programming_model.html](https://rocm.docs.amd.com/projects/HIP/en/latest/understand/programming_model.html)
- **Ideia-chave:** HIP é a abstração C/C++ paralela tipo CUDA da AMD — modelo SIMT com warps de 64 threads em CDNA e 32 threads em RDNA, hierarquia de threads/blocks/grids, memória LDS/HBM, streams assíncronos. Bibliotecas: rocBLAS, MIOpen.
- **Relevância TCC:** Referência de origem para qualquer afirmação sobre o que HIP é e como difere de CUDA (notadamente o tamanho de wavefront variável). Critique no TCC a "compatibilidade superficial" entre os modelos.
- **Onde citar:** Cap. 3 (modelos de programação heterogênea).

### C.13 — AMD (2025) — Repositório oficial ROCm [validado_github]
- **Autor:** Advanced Micro Devices, Inc. — ROCm organization
- **Título:** ROCm: Open Source Software Stack for GPU Computation
- **Venue:** Repositório GitHub oficial (release ROCm 7.2.4)
- **URL:** [github.com/ROCm/ROCm](https://github.com/ROCm/ROCm)
- **Ideia-chave:** Meta-repo do stack ROCm. Componentes: HIP, LLVM, ROCR runtime; matemática (rocBLAS, hipBLAS, rocFFT, rocSPARSE, rocWMMA, hipTensor); ML/visão (Composable Kernel, MIOpen, MIGraphX, MIVisionX); comunicação (RCCL); profilers (ROCprofiler).
- **Relevância TCC:** Fonte primária para inventariar o que está disponível em ROCm vs análogos NVIDIA. Útil para tabela de paridade no Cap. 3.
- **Onde citar:** Cap. 3 (panorama do ecossistema AMD).

### C.14 — AMD (2025) — rocWMMA [validado_github]
- **Autor:** AMD ROCm Libraries Team
- **Título:** rocWMMA: C++ Header Library for Mixed-Precision MMA on AMD GPUs
- **Venue:** Repositório GitHub (release rocWMMA 2.2.0 para ROCm 7.2.4)
- **URL:** [github.com/ROCm/rocWMMA](https://github.com/ROCm/rocWMMA)
- **Ideia-chave:** Equivalente AMD à WMMA API da NVIDIA. Cobre Matrix Cores em CDNA (gfx908/90a/942/950) e AI Acceleration em RDNA 3 (gfx1100/1101/1102/1151) **e RDNA 4 (gfx1200/1201)**. Header-only.
- **Relevância TCC:** **Crucial** para discutir paridade real (não só formal) com Tensor Cores. Confirma que RDNA 4 — incluindo a RX 9070 XT — tem aceleração matricial via WMMA exposta no rocWMMA. **Trunfo central do TCC**.
- **Onde citar:** Cap. 3 (aceleradores matriciais AMD); Cap. 5 (oportunidades de otimização).

### C.15 — PyTorch Foundation (2025) — PyTorch ROCm [validado_doc_oficial, verificar versão]
- **Autor:** PyTorch Foundation
- **Título:** PyTorch — Get Started Locally (ROCm build)
- **Venue:** Documentação oficial PyTorch 2.7.0 / ROCm 6.3 (consulta jun/2026; **verificar versão atual antes do experimento**)
- **URL:** [pytorch.org/get-started/locally/](https://pytorch.org/get-started/locally/)
- **Ideia-chave:** PyTorch 2.7.0 estável distribui wheels oficiais para ROCm 6.3 em Linux. API segue idêntica à de CUDA (`torch.cuda.is_available()` continua funcionando), reduzindo barreira de migração de código.
- **Relevância TCC:** **ACHADO PRÓPRIO**: o build oficial estável referencia ROCm 6.3, enquanto o ROCm que reconhece RDNA 4 é o 7.x → defasagem PyTorch↔ROCm. Documentar como achado.
- **Onde citar:** Cap. 4 (setup experimental — caveat de versões); Cap. 5 (discussão).

### C.16 — Davis et al. (2024) — Performance Portability [validado_arxiv]
- **Autores:** Joshua H. Davis, Pranav Sivaraman, Joy Kitson, Konstantinos Parasyris, Harshitha Menon, Isaac Minn, Giorgis Georgakoudis, Abhinav Bhatele
- **Título:** Taking GPU Programming Models to Task for Performance Portability
- **Venue:** ACM (DOI 10.1145/3721145.3730423); arXiv preprint, 2024
- **arXiv:** [2402.08950](https://arxiv.org/abs/2402.08950)
- **Ideia-chave:** Compara sete modelos de programação GPU — CUDA, HIP, Kokkos, RAJA, OpenMP, OpenACC e SYCL — em cinco proxy apps científicas, em hardware NVIDIA e AMD. Documenta onde cada modelo perde desempenho.
- **Relevância TCC:** Referência empírica recente e independente para a tese central — quanto custa, em desempenho, escolher portabilidade em vez de CUDA nativo. **Inspiração metodológica direta** para o experimento.
- **Onde citar:** Cap. 3 (estado da arte); Cap. 4 (desenho experimental).

### C.17 — Heakl et al. (2025) — CASS Transpilation CUDA↔HIP [validado_arxiv, **revalidar**]
- **Autores:** Ahmed Heakl, Gustavo Bertolo Stahl, Sarim Hashmi, Seung Hun Eddie Han, Mukul Ranjan, Arina Kharlamova, Salman Khan, Abdulrahman Mahmoud
- **Título:** CASS: Nvidia to AMD Transpilation with Data, Models, and Benchmark
- **Venue:** arXiv preprint (cs.AR), 2025
- **arXiv:** [2505.16968](https://arxiv.org/abs/2505.16968)
- **Ideia-chave:** Solução de tradução source- e assembly-level (CUDA↔HIP, SASS↔RDNA3) treinada em 60 mil pares verificados. Reporta 88,2% de acurácia CUDA→HIP e 85% dos códigos com desempenho equivalente ao nativo.
- **Relevância TCC:** Demonstra que a fronteira CUDA↔HIP está se erodindo via ML. Relevante para discutir cenários futuros e como o experimento pode reaproveitar código CUDA existente (Instant-NGP, 3DGS).
- **Onde citar:** Cap. 5 (discussão); Cap. 6 (trabalhos futuros).
- **Atenção:** Paper recente — verificar antes de citar.

### C.18 — Chen; Ibrahim; Liu (2026) — VkSplat [validado_arxiv, **revalidar — paper recente**]
- **Autores:** Jingxiang Chen, Mohamed Ibrahim, Yang Liu
- **Título:** VkSplat: High-Performance 3DGS Training in Vulkan Compute
- **Venue:** Eurographics 2026 — Short Papers (a confirmar)
- **arXiv:** [2605.00219](https://arxiv.org/abs/2605.00219)
- **URL repo:** github.com/harry7557558/vksplat
- **Ideia-chave:** Pipeline de **TREINAMENTO** de 3D Gaussian Splatting integralmente em Vulkan compute, cross-vendor. Reporta 3,3x speedup e 33% menos VRAM contra baseline CUDA+PyTorch, mantendo qualidade.
- **Relevância TCC:** **A referência mais alinhada possível ao experimento.** Evidência publicada de que 3DGS treinável fora do CUDA não só funciona como pode SUPERAR o baseline em certas métricas. Validar replicação na RX 9070 XT.
- **Onde citar:** Cap. 4 (trabalhos correlatos); Cap. 5 (discussão).
- **Atenção:** Paper muito recente — **abrir o arXiv e o repo pessoalmente** antes de fazer planejamento experimental em cima. Se confirmado, é candidato a baseline forte.

### C.19 — Iandola et al. (2025) — SqueezeMe [validado_arxiv]
- **Autores:** Forrest Iandola, Stanislav Pidhorskyi, Igor Santesteban, Divam Gupta et al.
- **Título:** SqueezeMe: Mobile-Ready Distillation of Gaussian Full-Body Avatars
- **Venue:** SIGGRAPH 2025 (a confirmar)
- **arXiv:** [2412.15171](https://arxiv.org/abs/2412.15171)
- **Ideia-chave:** Pipeline de splatting baseado em Vulkan para renderizar 3 avatares Gaussianos full-body a 72 FPS num Meta Quest 3. Destila correctivos neurais para camadas lineares.
- **Relevância TCC:** Evidência de que Vulkan é alternativa viável NÃO só para fora-da-NVIDIA, mas para target classes inteiras (mobile/VR) onde CUDA é inviável. Argumento forte para a conclusão.
- **Onde citar:** Cap. 5 (discussão de aplicações práticas).

### C.20 — Battarbee et al. (2024) — Vlasiator NVIDIA+AMD [validado_arxiv]
- **Autores:** Markus Battarbee, Konstantinos Papadakis, Urs Ganse, Jaro Hokkanen, Leo Kotipalo, Yann Pfau-Kempf, Markku Alho, Minna Palmroth
- **Título:** Porting the grid-based 3D+3V hybrid-Vlasov kinetic plasma simulation Vlasiator to heterogeneous GPU architectures
- **Venue:** ASTRONUM 2024
- **arXiv:** [2406.02201](https://arxiv.org/abs/2406.02201)
- **Ideia-chave:** Estudo prático de port de simulação científica para CUDA+HIP usando codebase única. Documenta gerenciamento de memória esparsa e redesenho de kernels para wavefronts AMD vs warps NVIDIA.
- **Relevância TCC:** Exemplo concreto de portabilidade real (não-toy) NVIDIA↔AMD em produção HPC. Inspiração metodológica para o port do experimento de NeRF/3DGS.
- **Onde citar:** Cap. 4 (metodologia); Cap. 5 (discussão).

### C.21 — Tandon et al. (2024) — MI300A OpenMP [validado_arxiv]
- **Autores:** Suyash Tandon, Leopold Grinberg, Gheorghe-Teodor Bercea, Carlo Bertolli, Mark Olesen, Simone Bnà, Nicholas Malaya
- **Título:** Porting HPC Applications to AMD Instinct MI300A Using Unified Memory and OpenMP
- **Venue:** ISC High Performance 2024
- **arXiv:** [2405.00436](https://arxiv.org/abs/2405.00436)
- **Ideia-chave:** MI300A é o primeiro APU de datacenter da AMD com memória unificada entre Zen 4 EPYC e CDNA 3. Demonstra port de OpenFOAM via OpenMP unified memory.
- **Relevância TCC:** Estabelece o "topo de linha" do ecossistema AMD para HPC/IA. Útil para situar a RDNA 4 (consumer) em relação ao CDNA 3 (datacenter).
- **Onde citar:** Cap. 3 (panorama AMD CDNA vs RDNA).

### C.22 — Yan et al. (2020) — Demystifying Tensor Cores [fonte_primaria_inacessivel]
- **Autores:** Da Yan, Wei Wang, Xiaowen Chu
- **Título:** Demystifying Tensor Cores to Optimize Half-Precision Matrix Multiply
- **Venue:** IEEE IPDPS 2020 — DOI 10.1109/IPDPS47924.2020.00071
- **arXiv:** não localizado
- **Ideia-chave:** Engenharia reversa dos Tensor Cores Volta/Turing via microbenchmarks PTX/SASS. Mostra latências, throughput e escalonamento por warp; base de muitos otimizadores GEMM half-precision posteriores.
- **Relevância TCC:** Referência canônica usada na literatura para comparações cross-vendor de unidades de matriz.
- **Onde citar:** Cap. 3 (aceleradores matriciais).
- **Pendência:** IEEE Xplore atrás de paywall. Substituível por **Sun et al. 2022 (C.7)** ou **Abdelkhalik et al. 2022 (C.8)** se inacessível no depósito.

---

## Eixo D — Datasets de Avaliação

### D.1 — Synthetic-NeRF (Mildenhall et al. 2020) — ver A.1
Dataset de 8 cenas Blender introduzido junto com o NeRF original. Padrão para benchmark de qualidade.

### D.2 — Mildenhall et al. (2019) — LLFF [validado_arxiv]
- **Autores:** Ben Mildenhall, Pratul P. Srinivasan, Rodrigo Ortiz-Cayon, Nima Khademi Kalantari, Ravi Ramamoorthi, Ren Ng, Abhishek Kar
- **Título:** Local Light Field Fusion: Practical View Synthesis with Prescriptive Sampling Guidelines
- **Venue:** SIGGRAPH 2019 / ACM ToG
- **arXiv:** [1905.00889](https://arxiv.org/abs/1905.00889)
- **Ideia-chave:** Pipeline MPI para síntese de vistas com diretrizes de amostragem. Introduz o **dataset LLFF** (cenas forward-facing reais).
- **Relevância TCC:** Dataset benchmark padrão em quase todo paper NeRF — cenas forward-facing reais, complementam o sintético.
- **Onde citar:** Cap. 4 (datasets de avaliação).

### D.3 — Mip-NeRF 360 dataset (Barron et al. 2022) — ver B.5
Dataset de cenas indoor/outdoor 360° introduzido em Mip-NeRF 360. Benchmark canônico para 3DGS.

### D.4 — Yeshwanth et al. (2023) — ScanNet++ [validado_arxiv]
- **Autores:** Chandan Yeshwanth, Yueh-Cheng Liu, Matthias Nießner, Angela Dai
- **Título:** ScanNet++: A High-Fidelity Dataset of 3D Indoor Scenes
- **Venue:** ICCV 2023
- **arXiv:** [2308.11417](https://arxiv.org/abs/2308.11417)
- **Ideia-chave:** 460 cenas indoor com laser scanner sub-mm + DSLR 33MP + RGB-D iPhone, com benchmarks oficiais de novel view synthesis e segmentação semântica.
- **Relevância TCC:** Dataset relativamente recente, oferece benchmark NVS com ground-truth de altíssima qualidade — bom para avaliar 3DGS/NeRF em condições controladas e robustez cross-hardware.
- **Onde citar:** Cap. 4 (datasets de avaliação).

### D.5 — Knapitsch et al. (2017) — Tanks and Temples [fonte_primaria_inacessivel]
- **Autores:** Arno Knapitsch, Jaesik Park, Qian-Yi Zhou, Vladlen Koltun
- **Título:** Tanks and Temples: Benchmarking Large-Scale Scene Reconstruction
- **Venue:** ACM Transactions on Graphics (SIGGRAPH 2017) — atribuição amplamente reportada, **NÃO confirmada em fonte primária acessível**
- **URL repo:** [github.com/isl-org/TanksAndTemples](https://github.com/isl-org/TanksAndTemples)
- **Ideia-chave:** Benchmark de reconstrução 3D em larga escala com ground-truth obtido por scanner industrial. Conjunto canônico de cenas (Truck, Train, Barn, etc.).
- **Relevância TCC:** Benchmark padrão usado por 3DGS e Mip-NeRF 360 — provavelmente compõe o experimento.
- **Onde citar:** Cap. 4 (datasets).
- **Pendência:** validar autores/ano no site oficial tanksandtemples.org (fora da allowlist) ou ACM DL antes da redação final.

### D.6 — Jensen et al. (2014) — DTU MVS [fonte_primaria_inacessivel, opcional]
- **Autores:** Rasmus Jensen, Anders Dahl, George Vogiatzis, Engin Tola, Henrik Aanaes (atribuição não confirmada nesta sessão)
- **Título:** Large Scale Multi-view Stereopsis Evaluation
- **Venue:** CVPR 2014 (versão estendida em Aanaes et al., IJCV 2016, "Large-Scale Data for Multiple-View Stereopsis")
- **Ideia-chave:** 124 cenas com ground-truth de scanner estruturado, padrão para multi-view stereo, adotado por NeRF/3DGS em avaliações de geometria.
- **Relevância TCC:** Opcional se o experimento focar qualidade de imagem (PSNR/LPIPS); essencial se for incluir reconstrução de superfície.
- **Onde citar:** Cap. 4 (datasets), opcional.

---

## Itens com fonte primária inacessível (revalidar manualmente)

Antes do depósito, confirmar paginação, autoria e venue dos seguintes em PDFs originais (acessar via biblioteca da UFC ou IEEE Xplore/ACM DL via VPN institucional):

- **A.12** WANG et al. (2004) — SSIM (IEEE TIP)
- **A.13** KAJIYA; VON HERZEN (1984) — Volume rendering (SIGGRAPH '84, ACM)
- **A.14** WESTOVER (1990) — Splatting (SIGGRAPH '90, ACM)
- **C.22** YAN et al. (2020) — Demystifying Tensor Cores (IEEE IPDPS)
- **D.5** KNAPITSCH et al. (2017) — Tanks and Temples (ACM ToG)
- **D.6** JENSEN et al. (2014) — DTU MVS (CVPR 2014)

## Itens recentes — abrir e validar antes de citar

Papers de 2025-2026 que valem confirmar pessoalmente no arXiv antes de incorporar à redação:

- **C.10** XIE et al. (2025) — Bit-Accurate MMA — `arxiv.org/abs/2511.10909`
- **C.17** HEAKL et al. (2025) — CASS — `arxiv.org/abs/2505.16968`
- **C.18** CHEN; IBRAHIM; LIU (2026) — VkSplat — `arxiv.org/abs/2605.00219` ← **alvo metodológico crítico, abrir primeiro**
- **C.19** IANDOLA et al. (2025) — SqueezeMe — `arxiv.org/abs/2412.15171`

## Lista de leitura prioritária para o aluno

Como orientador, esta é a ordem sugerida de leitura para começar a escrever:

**Sprint 1 — preparar Cap. 2 (fundamentação):**
1. A.1 NeRF — paper original
2. A.6 3DGS — paper original
3. A.7 Instant-NGP — paper de referência da aceleração
4. A.10 Tewari et al. 2022 (STAR) — survey para amarrar a narrativa
5. A.11 Chen & Wang 2024 — survey 3DGS
6. A.8 Zhang et al. 2018 (LPIPS) — métricas

**Sprint 2 — preparar Cap. 3 (hardware/portabilidade):**
1. C.1, C.2 Hu et al. (Taichi original e DiffTaichi)
2. C.6 Markidis et al. — Tensor Cores (histórico)
3. C.16 Davis et al. 2024 — performance portability (inspiração metodológica)
4. C.11, C.12, C.14 — docs oficiais ROCm, HIP, rocWMMA
5. C.18 VkSplat (depois de validar) — trabalho correlato direto

**Antes do experimento (Sprint 0/3):**
1. C.4 Linyou taichi-ngp-renderer — código de partida para NeRF
2. PR #1297 do gaussian-splatting — código de partida para 3DGS (issue rastreada em `reference_experimento_rdna4` da memória)
3. C.18 VkSplat (validar e ler na íntegra) — possível baseline alternativo
4. B.13 NVlabs/tiny-cuda-nn — entender o adversário a substituir

## Domínios adicionais a liberar (para próxima rodada)

Para fechar pendências e validar venues:

- `dl.acm.org` — Kajiya 1984, Westover 1990, Knapitsch 2017, Hu 2019 (TOG), DOI canônico de SIGGRAPH/ToG
- `ieeexplore.ieee.org` — Wang 2004 (SSIM), Yan 2020
- `openaccess.thecvf.com` — Mip-NeRF, Mip-NeRF 360, Plenoxels, DVGO, TensoRF, BARF, ScanNet++, 4DGS
- `proceedings.neurips.cc` — SRN (Sitzmann 2019), NeuS (Wang 2021)
- `diglib.eg.org` — STARs Tewari 2020/2022 nos anais oficiais
- `developer.nvidia.com` — DLSS, Hopper, Blackwell, CUDA Programming Guide
- `gpuopen.com` — RDNA ISA, RDNA 3 WMMA, FidelityFX
- `www.khronos.org` / `docs.vulkan.org` — Vulkan compute spec
- `tanksandtemples.org` — site oficial Tanks and Temples
- `roboimagedata.compute.dtu.dk` — DTU MVS oficial
- `scholar.google.com` — descoberta cruzada (search direto via google.com falhou em algumas tentativas)
