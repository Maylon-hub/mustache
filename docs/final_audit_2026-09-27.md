# Auditoria final do MustaCHE - 27/09/2026

Documento de entrega interna; a interface, o README, o guia e o site público permanecem em inglês. O resumo executivo está em `final_summary_2026-09-27.md` e foi diagramado separadamente em duas páginas.

## Escopo, estado e conclusão

MustaCHE: branch `mustache-core-sg`, HEAD `40507f8e`; CORE-SG: branch `develop`, HEAD `f5a716b`. Ambos já continham alterações da revisão anterior. Elas foram preservadas, e os HEADs não mudaram. Portanto, esses commits sozinhos **não identificam todo o código auditado**: é necessário conservar o diff e os arquivos novos. Nenhum commit, push, tag ou publicação foi realizado.

**Conclusão:** o fluxo principal está funcional e centrado no CORE-SG. A ferramenta está apta à avaliação local e à preparação de uma release candidata. A declaração de primeira release pública estável depende dos bloqueadores de distribuição e reprodução abaixo. Identidade numérica com o MustaCHE/RNG original não foi demonstrada e não é requisito implícito para uma ferramenta explicitamente centrada no CORE-SG.

Nesta etapa não houve mudança de algoritmo científico, formato persistido ou arquitetura. Foram consolidados textos, exemplos, defaults declarados e cobertura do caminho CORE-SG. Não foi encontrado um novo defeito crítico de execução nos cenários verificados.

## 1. Evidências do estado atual

Os caminhos abaixo são relativos à raiz do MustaCHE; `../core-sg/` identifica o segundo repositório. Os testes nomeados foram executados nesta auditoria, salvo indicação contrária. `TS` significa `tests/test_scientific_review.py`; `UI` significa `scripts/verify_web_ui.cjs`.

| Item | Arquivo e função/classe relevante | Evidência e teste | Conclusão / limite |
|---|---|---|---|
| CORE-SG principal | `mustache/core/batch.py::run_batch_clustering`; `clustering.py::run_clustering`; `routes.py::batch_process` e `upload_file`; templates `index.html`, `settings.html` | Default `algorithm='core-sg'`; TS `test_batch_endpoint_defaults_to_core_sg`; UI `fresh browser defaults to CORE-SG` | Confirmado. Preferências explícitas do usuário e projetos HDBSCAN salvos continuam respeitados. |
| Um suporte por batch | `mustache/core/batch.py::run_batch_clustering` | Instância e `fit(..., k_max=max_mpts)` antes do laço; TS `test_batch_fits_core_once_and_extracts_every_requested_mpts` registra uma instância, um fit e extrações 2,4,6 | Confirmado; o máximo configurado é usado mesmo se o step não o alcançar. |
| Reutilização efetiva | `mustache/core/clustering.py::run_clustering`; `../core-sg/core_sg/core_sg.py::CoreSG.extract_hierarchy_from_core_sg`, `extract_mst_from_core_sg` | Mesmo objeto; `support_graph_`, `metric_edges_`, `core_distances_` reutilizados. `tests/unit/test_core_sg_hierarchy.py::TestCoreSGHierarchy.test_standalone_mst_keeps_complete_k_max_support_graph` e `test_extracting_smaller_k_updates_current_artifacts_without_mutating_k_max` | Confirmado; k_max pode retornar artefatos calculados no fit. Não há reconstrução por mpts no batch. |
| HAI principal | `mustache/core/hai.py::compute_hai_matrix`; `batch.py::analyze_batch_results`; `main.js::renderHAI` | TS `test_hai_known_original_pair_sum` (23/27), `test_sampled_hai_preserves_normalization_and_metadata`; `tests/test_hai.py::TestComputeHAIMatrix` cobre simetria, diagonal, intervalo e versão densa | Confirmado para as árvores fornecidas. TED/ARI/AMI/DBCV não substituem HAI; representação legada exige validação separada. |
| Medoides | `mustache/core/hai.py::compute_medoids`; `batch.py::analyze_batch_results`; `routes.py::cut_dendrogram`; `main.js::renderReachability` | TS `test_medoid_minimizes_within_cluster_distance_and_ties`, `test_root_branch_contains_all_hierarchies`, `test_manual_groups_update_medoids_and_persist` | Minimiza soma de 1-HAI no meta-cluster; empate pelo primeiro mpts ordenado; ruído automático separado. |
| Reachability por hierarquia | `mustache/core/clustering.py::hierarchy_reachability`; `main.js::renderReachability`, `inspectHierarchy` | TS `test_reachability_is_adjacent_cophenetic_of_this_tree` verifica `[None,2,9,3]`; `test_supported_metric_full_pipeline` confere mpts, métrica e ordenação; UI inspeciona mpts e restauração | Confirmado como contorno da árvore atual. Não é OPTICS e não é uma afirmação de igualdade das barras do legado. |
| Propagação das métricas | `routes.py::batch_process`; `validation.py::validate_metric`; `batch.py::run_batch_clustering`; `clustering.py::run_clustering` | TS `test_supported_metric_full_pipeline` (2 motores x 5 métricas), `test_core_public_unrounded_matches_reference_mst_and_labels`, `test_invalid_metric_rejected_before_clustering`, `test_zero_vectors_rejected_for_cosine` | Euclidean, Manhattan, Chebyshev, Minkowski p=2 e Cosine exercitadas. Testes pequenos não constituem prova universal de equivalência. t-SNE Euclidean é apenas visualização. |
| Persistência e restauração | `storage.py::save_project`, `load_project`, `restore_params`; `routes.py::save_project_route`, `get_project_data`; `main.js::updateProjectInfo` e evento `mustache:project-loaded` | TS `test_saved_project_restores_parameters_partition_and_plots` agora nos dois motores; `test_old_project_parameter_fallback`, `test_cached_cut_updates_saved_partition`; UI salva/reabre/exporta com CORE-SG | Nome, dataset, n, algoritmo, min/max, step, métrica, tempo, HAI/metadados, linkage, labels, medoides, seleção, resultados e plots preservados. Dados ausentes em projetos antigos não podem ser inventados. |
| Inglês público | `mustache/templates/`, `static/js/main.js`, `routes.py`, `cli.py`; `README.md`, `docs/index.md`, `guia_documentacao.md`, `reproducao.md`; notebook | TS `test_ui_labels_and_metric_form`, rotas/assets no UI; revisão textual e busca de termos portugueses; MkDocs `--strict` | Confirmado nas superfícies principais inspecionadas. Não há teste capaz de provar linguisticamente toda mensagem de bibliotecas. Legado, manuscrito, contexto e esta entrega interna preservam o idioma original e ficam fora do site. |

### Papel exato do HDBSCAN

A opção `algorithm='hdbscan'` é o baseline auxiliar. Separadamente, o projeto utiliza componentes HDBSCAN dentro do caminho CORE-SG: `../core-sg/core_sg/hdbscan_adapter.py::fit_euclidean_reference`/`reference_mst_original_distance` participam da construção inicial; conversão de árvore, rotulagem e wrappers também usam a biblioteca. `mustache/core/hai.py::run_meta_clustering` usa o HDBSCAN do scikit-learn sobre objetos-hierarquia.

Assim, "HDBSCAN apenas baseline" é correto para o papel da opção de motor, mas não significa ausência de dependência algorítmica interna. Remover esses componentes seria outra intervenção, desnecessária nesta consolidação. A extração interativa continua organizada em torno do suporte CORE-SG reutilizável.

## 2. Original versus atual

Referências históricas verificadas: `legacy/mustache/templates/home/index.html`; `views/dashboard.py`; `views/api.py`; `tasks/tasks.py`; `resources/run.sh`; `resources/hierarchies.py`; `resources/hai.pyx`; `resources/hierarchy_tree.pyx`; `resources/hierarchy.pyx`; `static/js/dashboard/myplots.js`; `legacy/README.rst`. A classificação descreve comportamento, sem tratar toda diferença como defeito.

| Funcionalidade | Original | Atual | Status | Observação |
|---|---|---|---|---|
| Seleção de dataset | Upload e workspace de datasets/projetos | CSV e catálogo Iris, Wine, Breast Cancer, Moons, Circles e Blobs | Melhorado | Dados sintéticos usam seed 42; CSV permite declarar cabeçalho. |
| min mpts | Campo no formulário; launcher observado fixa início em 2 | Limite inferior efetivamente usado no batch | Melhorado | Preserva a intenção e corrige a inconsistência histórica observada. |
| max mpts | Campo e parâmetro Java; loader Python usa `range(kmin,kmax,skip)` | Limite inclusivo se alcançado pelo step; suporte em max_mpts | Alterado | Igualdade dos limites exibidos não implica mesma lista de hierarquias. |
| step | `skip=1` interno; sem seletor equivalente encontrado | Step size explícito | Melhorado | Lista efetiva registrada em `ordered_mpts`. |
| Distance metric | euclidean, angular, pearson, manhattan, supremum | euclidean, manhattan, chebyshev, minkowski p=2, cosine | Alterado | Não há correspondência automática angular=cosine ou pearson; aliases não são oferecidos. |
| Tamanho mínimo de cluster | Campo independente `datasetMinCluster` | Batch o vincula a mpts; API individual permite separação | Alterado | Pode mudar partições planas; documentado. |
| HAI | Soma normalizada de diferenças das distâncias de hierarquia | Mesma fórmula; exato e amostrado identificados | Precisa validação | Caso pequeno conhecido e invariantes passam; saída integral Java não foi reproduzida. |
| Meta-clustering | HDBSCAN nativo sobre 1-HAI, referência e min_samples=1 | scikit-learn HDBSCAN, min_samples=1, min_cluster_size=2, allow_single_cluster=True | Alterado | Seleção automática não promete a mesma partição padrão. |
| Meta-dendrogram | Árvore de single linkage do meta-clustering | SciPy single linkage em 1-HAI | Preservado | Intenção e distância preservadas; layout/empates podem variar. |
| Medoides | `compute_medoid_elements`: menor soma de distâncias no grupo | Mesmo critério, mpts identificado e explicação visível | Preservado | Representante pode mudar se HAI ou o meta-cluster mudar. |
| Reachability Plots | Intervalos/níveis da hierarquia Java, ordenação própria, primeira barra artificial | Alturas cophenéticas entre folhas adjacentes da árvore escolhida; primeira barra indefinida | Alterado | Cada mpts tem seus próprios dados; comparação numérica com o legado permanece aberta. |
| FOSC | Arquivo FOSC, ramos automáticos e integração visual | Seleção automática via HDBSCAN; sem paridade completa de controles/configuração FOSC | Alterado | Há seleção por estabilidade; não afirmar ausência absoluta de FOSC nem reprodução integral. |
| Threshold | Corte por distância | Corte em 1-HAI, cache coerente e persistência | Preservado | Teste cobre igualdade exata no nível de fusão. |
| Seleção manual | Ramos definem grupos de hierarquias/representantes | Grupos de descendentes não sobrepostos, medoides atualizados, seleção salva/exportada | Preservado | Sobreposições substituem grupos anteriores; não são seleção de pontos. |
| Persistência de projetos | Workspace, settings e resultados gerados | JSON/CSV com parâmetros, proveniência e geometria completa | Melhorado | Fallback para versões anteriores do formato moderno; importação automática do workspace legado não foi entregue. |
| Exportação | Arquivos e controles; endpoint ZIP encontrado contém placeholder | CSV de hierarquias selecionadas e ZIP de projeto | Melhorado | Exportação CSV foi exercitada no navegador; não alegar paridade de todo export legado. |
| RNG | Pipeline Java e opções de filtro RNG | Não integrado ao fluxo moderno | Ausente | Substituição intencional pelo CORE-SG; comparação experimental ainda não reproduzida. |
| CORE-SG | Não faz parte do motor histórico | Motor principal e suporte reutilizado | Melhorado | Amplia o foco da ferramenta; não implica superioridade universal. |
| HDBSCAN | Família científica, implementação Java e meta-clustering nativo | Baseline de motor e componentes internos de suporte/meta-análise | Alterado | Papel de baseline não elimina a biblioteca das dependências. |
| Interface web | Flask, D3, Celery/Redis no fluxo legado | Flask/Plotly, execução local e síncrona | Alterado | Interação preservada; execução em background não foi reproduzida. |
| Idioma | UI principalmente em inglês | UI e documentação principal em inglês | Preservado | Histórico e documentação interna podem permanecer em português. |
| Instalação/distribuição | Docker recomendado, Java e dependências históricas | Pacote Python/CLI, CORE-SG com extensões nativas, workflows de candidatos | Alterado | Wheel/sdist construídos; instalação limpa do par final ainda pendente. |

O checkout contém `legacy/mustache/resources/IHDBSCAN.jar` (24.359.366 bytes). A alegação histórica de indisponibilidade não deve ser repetida como ausência atual do arquivo. Presença não demonstra que o pipeline Java/RNG seja executável ou corresponda ao artefato original; não foi executado aqui.

## 3. Diferenças científicas relevantes

Categorias: **A** aceitável e intencional; **B** precisa ser corrigida; **C** precisa apenas ser documentada; **D** precisa de validação experimental. Uma mudança intencional pode ter uma alegação de equivalência separada que exija D.

| Diferença | Consequência analítica | Classe | Tratamento |
|---|---|---|---|
| RNG substituído por CORE-SG | Construção e reutilização do suporte mudam | A | É o objetivo do projeto. Explicitar escopo e parâmetros. |
| Alegar equivalência/desempenho CORE-SG versus RNG nesta integração | Pode sustentar conclusões experimentais indevidas | D | Reproduzir artefatos/datasets e cargas comparáveis; HDBSCAN não prova equivalência a RNG. |
| Hierarquia Java por intervalos/folhas terminais versus full single linkage moderno | Pode alterar d_H e, consequentemente, HAI e meta-clusters | D | Comparar representações e resultados conhecidos. A fórmula HAI segue intacta. |
| Amostragem de pares no HAI acima do limiar | Pequenas diferenças podem mudar partições e medoides | D | Método/seed/budget/bound já documentados; validar estabilidade do uso científico pretendido. |
| min_cluster_size vinculado a mpts no batch | Modifica seleção de grupos e ruído em comparação com configuração independente | C | Política atual documentada; desacoplar é evolução possível, não correção automática nesta etapa. |
| Limites efetivos e step diferentes do launcher original | Conjunto de hierarquias explorado pode variar | C | Comparar `ordered_mpts`, não somente os números da sidebar. |
| Defaults e biblioteca do meta-clustering/FOSC | Partição automática diferente pode selecionar outros representantes | C | Documentar min_samples, min_cluster_size e single-cluster allowance; equivalência estrita exigiria experimento próprio. |
| Reachability derivado da árvore atual, primeira barra indefinida | Escalas, ordem e barras podem diferir do legado | C | Identificado como contorno da hierarquia; oráculo atual testa a geometria. Igualdade histórica não é afirmada. |
| Conjunto de métricas e ausência de preprocessing automático | Trocar dissimilaridade ou escala das features altera árvores e HAI | C | Usar a mesma métrica e preparação ao comparar; Minkowski atual é p=2; cosine rejeita vetor zero. |
| Empates do medoide e separação de outliers | Empates determinísticos; excluídos não representam grupos | A | Mesmo critério de minimização; nenhuma redefinição do medoide foi encontrada. |

Não foi identificada nesta etapa uma diferença científica da categoria B que justificasse nova refatoração. Isso não converte as linhas D em resultados demonstrados.

Correção da revisão anterior: chamar toda a saída legada de "compacta" era impreciso. `tasks.py` passa `compact=False` ao Java. A diferença comprovada está no tratamento de intervalos/folhas terminais em `HierarchyTree`; a interpretação completa do arquivo Java permanece sem reprodução. O guia e a revisão anterior receberam esclarecimento explícito.

## 4. Checklist de primeira release pública estável

### Bloqueadores

- [ ] **Congelar a versão entregável nos dois repositórios.** Revisar e versionar o diff atual, escolher números ainda não usados e alinhar pyproject, CITATION, tag e release notes. Os candidatos atuais 0.3.0rc2/0.4.5rc2 não são uma nova release estável com estas correções.
- [ ] **Instalação limpa do par final.** Produzir o CORE-SG corrigido e instalar os artefatos MustaCHE + CORE-SG fora dos checkouts, sem PYTHONPATH; executar pip check, exemplos, testes e fluxo web nos sistemas/Pythons anunciados. O wheel MustaCHE local não valida sozinho as extensões CORE-SG.
- [ ] **Verificação automática antes de publicar.** O MustaCHE tem workflows de Pages e TestPyPI, mas não há workflow de testes de PR/push nem publicação estável PyPI no checkout inspecionado. O workflow TestPyPI constrói/verifica metadata e publica sem rodar pytest. Definir um gate de testes e o caminho estável com Trusted Publisher correto.
- [ ] **Identidade e registro da release.** Falta changelog/release notes. CITATION tem o artigo original e versão candidata, mas os autores de software listados são apenas os autores históricos; revisar atribuição da modernização e alinhar a citação da release. Registrar o perfil científico e suas limitações na entrega estável.
- [ ] **Confirmar os destinos publicados.** Instalação a partir do índice escolhido e conteúdo real do Pages precisam ser conferidos após a publicação da release. As consultas desta auditoria deram timeout; não indicam ausência nem sucesso de publicação.

### Importantes, não bloqueantes para uma release local com escopo declarado

- [x] CORE-SG principal em defaults, README, guia, landing page, exemplos e seletores; HDBSCAN disponível como baseline.
- [x] HAI, medoides, métricas, restauração e batch reutilizado cobertos por testes; confirmação CORE-SG no navegador.
- [x] Inglês das superfícies principais; docs compilam estritamente; catálogo reproduzível; notebook e exemplo executam.
- [ ] Documentar origem/licença dos datasets e preparar um conjunto pequeno de aceitação sem depender de screenshots antigas.
- [ ] Revisar a faixa de versões suportadas: o wrapper usa `_tree_to_labels`, API privada do HDBSCAN. Fixar um conjunto verificado ou testar limites das dependências anunciadas.
- [ ] Conferir avisos de terceiros e atribuições de assets. A licença BSD-3-Clause existe; isso não é um inventário completo de direitos de todos os itens em legacy/.
- [ ] Fazer aceitação humana dos cliques nos ramos, mobile e importação de projetos antigos. O teste automatizado de ramo emite evento Plotly; não prova hit-testing físico.
- [ ] Integrar com MIDAS via revisão/PR e definir manutenção, versões e documentação canônica. CORE-SG já configura upstream `https://github.com/midas-core-sg/core-sg`; upstream configurado não significa integração aceita. Para publicar sob MIDAS, a aceitação passa a ser pré-condição organizacional.
- [ ] Arquivar a release identificada no Zenodo e emitir DOI de software; manter separado do DOI do artigo original. DOI não é requisito técnico para publicar um pacote estável.

### Trabalho futuro / artigo

- [ ] Reprodução Java/RNG, fixtures de representação e análise da diferença no HAI.
- [ ] Benchmarks de cargas equivalentes e múltiplas execuções; estabilidade de HAI amostrado e dos meta-clusters.
- [ ] Controles FOSC/meta-clustering mais completos e min_cluster_size independente no batch.
- [ ] Expor visualmente mais artefatos próprios do CORE-SG (suporte/MST/profiling); SCORE-SG, se fizer parte do escopo futuro.
- [ ] Redução de memória quadrática, sessões multiusuário e processamento assíncrono, conforme demanda.

## 5. Verificação executada e limites

| Verificação desta auditoria | Resultado |
|---|---|
| Suíte completa MustaCHE no checkout atualizado | **113 passaram em 13,93 s**; XML `audit-mustache-actual-20260927.xml` |
| CORE-SG: `test_core_sg_hierarchy.py` e `test_public_euclidean_reference.py` | **24 passaram em 3,62 s**; XML `audit-core-sg-20260927.xml` |
| Navegador, CORE-SG/Iris/Manhattan/mpts 2..10/step 2 | **39 verificações passaram**; análise, default, medoide manual, inspeção, salvar/reabrir, CSV, assets, overflow básico; sem erros JS/HTTP capturados |
| Exportação ZIP | Projeto do teste exportado pela API: metadata.json, results.json e data.csv; algoritmo CORE-SG, Manhattan e ordered_mpts preservados |
| Exemplos | Células de código do notebook e exemplo Python do README executados; 90 amostras/3 hierarquias no notebook. Nesta etapa não foi aberto novo kernel Jupyter |
| Documentação | MkDocs `--strict` passou; fontes públicas principais revisadas em inglês |
| Empacotamento MustaCHE | Wheel e sdist 0.3.0rc2 construídos em cópia temporária com runtime de build separado; são artefatos locais de auditoria, não releases |
| Integridade | `git diff --check` passou; bibliografia preservada; nenhum reset ou remoção de alterações |

Os **204 testes completos CORE-SG** pertencem à revisão anterior; não foram todos reexecutados nesta etapa. Aqui o backend não foi alterado e foram escolhidos os 24 testes diretamente relevantes. Os testes dos dois motores contra HDBSCAN são controles delimitados, não uma obrigação de fazer CORE-SG imitar todo comportamento do baseline.

Runtime científico: Python 3.11.0, hdbscan 0.8.44, scikit-learn 1.9.1; imports direcionados aos dois checkouts e arquivos identificados. A metadata instalada agora informa MustaCHE 0.3.0 e CORE-SG 0.4.4; a metadata do código é 0.3.0rc2/0.4.5rc2. `pip check` da instalação existente passa, mas não comprova instalação das fontes corrigidas nem compatibilidade do par candidato. O build utilizou o runtime Python 3.12 e setuptools/wheel disponíveis no ambiente de ferramentas; o venv científico não tinha `bdist_wheel`.

As primeiras tentativas de build e acesso aos artefatos tiveram restrição de permissões Windows; foram repetidas com autorização no diretório temporário. A consulta ao PyPI/Pages foi tentada também fora do sandbox e terminou em timeout. Não se atribuem essas falhas ambientais ao algoritmo.

Evidências locais: `C:/Users/guest/Documents/Codex/audit-ui-evidence-20260927/` (JSON, screenshots e CSV); XMLs em `C:/Users/guest/Documents/Codex/`; builds em `audit-dist-20260927/`; site em `audit-docs-site-20260927/`. Os projetos usados pelos testes ficam em diretório isolado.

As cópias interna e externa de `relatorio_autocontido_sem_biber.tex` continuam com SHA-256 `162277314EFAE1D3518657B2B6A70B6E5516E3C4E49E596426A5A94B53D6D861`.

O wheel contém 30 entradas; assets essenciais, comando `mustache`, licença e metadata de dependências foram conferidos, com comparação dos arquivos essenciais contra o checkout. SHA-256 do wheel: `8ea41eb94b3efb728ee7cf4d6b842b8e2f9c4064dae65e783854c43069b16a3a`; sdist: `996a0a19a312583f2e94c07e312c5d7ae75bab41399f5c34d12d5f359b3a6f8b`. Esses hashes identificam apenas os artefatos locais desta auditoria.

## 6. Alterações desta consolidação

- `README.md`, `docs/index.md`, `docs/guia_documentacao.md`, `docs/reproducao.md`: CORE-SG primeiro, baseline explícito, dependências internas esclarecidas, política de parâmetros e diferença de representação documentadas.
- `docs/technical_review_2026-09-26.md`: esclarecimento da afirmação sobre compactação, preservando resultados históricos.
- `mustache/templates/{index,settings,dashboard,base}.html`: nomes de motor e baseline; o template antigo não é a rota principal, mas sua descrição foi corrigida.
- `mustache/core/batch.py`: somente comentários; removida promessa não medida de milissegundos e comparação imprecisa com parâmetros legados.
- `examples/mustache_quickstart.ipynb`: introdução centrada no CORE-SG; células científicas preservadas.
- `scripts/verify_web_ui.cjs`: CORE-SG como cenário padrão; opção HDBSCAN mantida; checagem do default do navegador.
- `tests/test_scientific_review.py`: restauração nos dois motores e teste explícito do endpoint sem algoritmo informado; total passou de 111 para 113.
- `mkdocs.yml`: esta auditoria e seu resumo interno ficam fora do site público em inglês.
- Novos documentos: esta auditoria e `final_summary_2026-09-27.md`, além do resumo PDF de duas páginas.

## Próximos cinco passos

1. Congelar o diff revisado dos dois repositórios e definir versões/releases coerentes com a dependência corrigida.
2. Construir e instalar o par de artefatos em ambiente limpo; repetir aceitação CORE-SG nos alvos anunciados.
3. Adicionar o gate de CI, finalizar changelog/release notes/CITATION e configurar o caminho estável PyPI.
4. Realizar aceitação independente com o orientador e preparar a integração/revisão MIDAS, preservando o escopo científico declarado.
5. Publicar pacote e Pages verificados; arquivar a release com DOI e planejar os experimentos RNG/HAI como trabalho científico identificado.
