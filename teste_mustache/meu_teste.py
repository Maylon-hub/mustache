import pandas as pd
import numpy as np
from mustache.core.clustering import run_clustering

print('==================================================')
print('Iniciando Teste do MustaCHE com Core-SG...')
print('==================================================')

# 1. Gerar dados sintéticos para agrupamento
np.random.seed(42)
dados = np.vstack([
    np.random.normal(loc=0.0, scale=0.5, size=(12, 2)),
    np.random.normal(loc=5.0, scale=0.5, size=(12, 2))
])
df = pd.DataFrame(dados, columns=['x', 'y'])

# 2. Executar o agrupamento
res = run_clustering(df, min_cluster_size=3, min_samples=3, algorithm='core-sg')

# 3. Mostrar os resultados
print(f'Sucesso! Grupos identificados: {res["n_clusters"]}')
print(f'Pontos considerados ruido: {res["noise_points"]}')
print('==================================================')
