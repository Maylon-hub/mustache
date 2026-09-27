# MustaCHE - auditoria final

27/09/2026 | Resumo executivo | Maylon Martins de Melo - orientação: Murilo Coelho Naldi

## Estado atual

O MustaCHE está funcional como ferramenta visual e interativa centrada no CORE-SG. API, batch, formulário e configurações usam esse motor por padrão. HDBSCAN permanece disponível como baseline auxiliar; sua biblioteca também fornece componentes internos de árvores e meta-clustering. Esses dois papéis precisam ser distinguidos.

O batch constrói uma única instância CORE-SG em k_max e reutiliza o suporte para extrair as hierarquias. HAI continua sendo a medida principal; medoides minimizam a soma de 1-HAI em cada meta-cluster. Os Reachability Plots usam a geometria da hierarquia indicada. Métrica, parâmetros, seleção e resultados são restaurados ao reabrir projetos.

## Evidências e correções consolidadas

Passaram 113 testes do MustaCHE no checkout atual, 24 testes focados no CORE-SG e 39 verificações no navegador com CORE-SG, Iris e Manhattan. O fluxo incluiu seleção manual, medoide, inspeção, salvar, reabrir e exportar. O exemplo do README e as células do notebook executaram; a documentação compilou em modo estrito. Wheel e sdist do MustaCHE foram construídos localmente.

A revisão anterior corrigiu HAI/metadados, convenções do CORE-SG, reutilização do suporte, reachability compartilhado indevidamente, sidebar, persistência e seleção. Esta auditoria fez apenas consolidação de textos, exemplos e cobertura do caminho CORE-SG. Não houve nova refatoração científica. A interface pública e a documentação principal permanecem em inglês.

## Diferenças em relação ao original

A substituição de RNG por CORE-SG é intencional. O HAI conserva sua fórmula, mas opera sobre árvores full single linkage; o leitor legado trata intervalos e folhas terminais de outra forma. A revisão anterior chamou essa representação de compacta de forma excessivamente ampla: o launcher inspecionado passa compact=False. Equivalência numérica completa não foi demonstrada.

O batch atual vincula tamanho mínimo de cluster a mpts; o formulário legado os separava. Defaults do meta-clustering e controles FOSC diferem. O reachability atual usa alturas entre folhas adjacentes e deixa a primeira barra indefinida. Há um IHDBSCAN.jar no checkout, mas a execução Java/RNG não foi validada.

<!-- pagebreak -->

## Riscos e prontidão para publicação

O projeto está apto à avaliação local e à preparação de uma release candidata. Ainda não há evidência suficiente para declarar a primeira release pública estável pronta.

Os bloqueadores são: congelar e versionar as alterações; alinhar as versões dos dois pacotes; instalar e testar o par corrigido em ambiente limpo; acrescentar testes ao fluxo de publicação; finalizar changelog, release notes e atribuição da citação de software; conferir os destinos publicados. O workflow MustaCHE inspecionado publica candidatos no TestPyPI, sem executar pytest, e não oferece ainda um caminho estável PyPI.

A instalação científica usada nos testes tem metadata diferente do código e recebeu os imports dos checkouts. O build MustaCHE não comprova a distribuição das extensões CORE-SG. As consultas ao PyPI e ao Pages terminaram em timeout, portanto seu estado remoto não foi confirmado.

Permanecem riscos delimitados: APIs privadas do HDBSCAN, memória quadrática, estado global de aplicação local, dependência de assets CDN e estabilidade da aproximação HAI. Identidade com RNG ou superioridade de desempenho exigem experimentos próprios; não bloqueiam uma release de escopo CORE-SG que declare suas limitações.

## Próximos cinco passos

1. Congelar o diff revisado e definir versões coerentes de MustaCHE e CORE-SG.
2. Construir e instalar os artefatos em ambiente limpo e repetir a aceitação nos alvos anunciados.
3. Finalizar CI, changelog, release notes, CITATION e publicação estável PyPI.
4. Fazer aceitação independente com o orientador e preparar a revisão de integração MIDAS.
5. Publicar pacote e Pages verificados; arquivar a release com DOI e planejar validação RNG/HAI.

## Registro da entrega

Branches preservadas: mustache-core-sg e develop. Alterações permanecem locais, sem commit, push ou publicação nesta etapa. A bibliografia autocontida foi preservada e conferida por checksum. A auditoria detalhada associa cada conclusão a arquivos, funções e testes e contém a matriz de comparação e o checklist de release.
