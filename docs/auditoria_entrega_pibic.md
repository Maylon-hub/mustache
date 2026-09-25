# Auditoria de entrega do PIBIC-Af - MustaCHE

Data da auditoria: 25/09/2026

Este documento separa três coisas que não devem ser confundidas no relatório final:

1. objetivos prometidos no projeto de 2025;
2. funcionalidades verificadas no checkout atual;
3. resultados históricos que precisam ser reproduzidos antes da assinatura.

## Objetivos do projeto e situação atual

| Objetivo original | Evidência atual | Situação |
|---|---|---|
| Integrar CORE-SG ao MustaCHE | `batch.py` constrói um modelo em `k_max` e reutiliza `extract_hierarchy_from_core_sg(k)` | Implementado e validado com wheels locais em ambiente limpo |
| Comparar desempenho antes/depois | Scripts e relatórios de benchmark presentes | Resultados históricos; precisam de repetição no ambiente final |
| Validar qualidade dos agrupamentos | ARI e AMI implementados quando há rótulos externos | Parcial: DBCV é citado no rascunho, mas não está implementado no checkout atual |
| Adaptar visualizações | Meta-dendrograma, HAI, reachability, corte e seleção manual | Implementado e validado no navegador |
| Atualizar documentação e treinamento | README, guia, notebook e relatório atualizados nesta auditoria | Implementado; resta a repetição independente pelo orientador |

## Evidências produzidas nesta auditoria

- 66 testes Pytest aprovados em Python 3.11.
- Notebook `examples/mustache_quickstart.ipynb` executado integralmente em kernel Python real.
- `mustache --help` validado e servidor iniciado pela CLI.
- Chrome headless validou `/`, `/datasets`, `/projects` e `/settings`.
- Todos os logos e assets das páginas testadas carregaram.
- Um lote HDBSCAN no dataset Iris gerou meta-dendrograma, matriz HAI e reachability plots.
- Seleção manual de um ramo retornou `mpts 4, 6`; limpar seleção funcionou.
- Nenhum erro grave foi observado no console do navegador.
- Smoke test reproduzível disponível em `scripts/verify_web_ui.py`.
- Wheels locais `mustache-core 0.3.0rc1` e `core-sg-mustache 0.4.5rc1` foram instaladas juntas em ambiente virtual limpo; as correções de publicação foram consolidadas nas candidatas `0.3.0rc2` e `0.4.5rc2`.
- Suíte independente do CORE-SG concluída com 200 testes aprovados.

## Correções aplicadas ao relatório final

1. Versões atualizadas para as candidatas `mustache-core 0.3.0rc2` e `core-sg-mustache 0.4.5rc2`.
2. Substituir “55 casos” pelo número produzido pela versão final da suíte. Nesta auditoria foram 66 testes.
3. Não afirmar que o meta-dendrograma usa `average/UPGMA`: o checkout atual usa single linkage.
4. Não afirmar que DBCV foi aplicada enquanto não houver implementação e resultados reproduzíveis. Hoje a aplicação calcula ARI e AMI com rótulos externos.
5. Remover a afirmação de containerização Docker multi-estágio como resultado da v2. O fluxo entregue atualmente é Python/pip e o Docker permanece apenas no legado.
6. Distinguir as wheels Cython atuais da wheel universal pure-Python descrita em uma etapa intermediária.
7. Atualizar a seção de reachability: o batch reutiliza uma execução de OPTICS. Isso melhora desempenho, mas os valores geométricos não são recalculados para cada `mpts`; apenas a coloração acompanha os rótulos da respectiva hierarquia.
8. Descrever o HAI escalável: exato e condensado até 2.000 amostras; amostragem determinística de pares acima disso, com metadados e limite de erro reportados.
9. Acrescentar a seleção manual por ramo: clique seleciona todas as folhas `mpts` da subárvore, a seleção é destacada, exportada e salva com o projeto.
10. Manter como resultado histórico, e não como nova evidência, qualquer benchmark que não tenha sido novamente executado no ambiente de entrega.

## Correções do backend CORE-SG

O carregamento de PyNNDescent/Numba passou a ser preguiçoso e ocorre somente quando o usuário
seleciona SCORE-SG. Também foi corrigida a extração para valores menores de `k`: o algoritmo
agora conserva o grafo de suporte completo construído para `k_max`, conforme a garantia do
CORE-SG, em vez de descartar vizinhos antes da reponderação. A suíte completa passou de 13
falhas de referência para 200 testes aprovados. O workflow de release foi consolidado para
evitar uploads duplicados e produzir wheels nativas para Linux, Windows e macOS.

## Critério sugerido para assinatura

Executar em uma máquina limpa, guardando terminal, versões e tempos:

1. criar ambiente virtual e instalar exatamente as versões publicadas;
2. executar `mustache --help` e iniciar a Web UI;
3. rodar os 66 testes;
4. executar o exemplo Python/notebook com HDBSCAN e CORE-SG;
5. executar um lote pequeno pela Web UI;
6. selecionar um ramo, salvar o projeto, recarregar e exportar o CSV;
7. executar pelo menos um cenário pequeno e um médio do benchmark;
8. confirmar que cada número e funcionalidade mencionados no relatório e no README aparecem nesse roteiro.
