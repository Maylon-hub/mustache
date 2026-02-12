import time
import tracemalloc
import pandas as pd
from sklearn.cluster import HDBSCAN
from sklearn.datasets import make_blobs

# Configuração
SIZES = [1000, 10000, 50000, 100000]
DIMENSIONS = [2, 10, 50]
RESULTS = []

print("Iniciando Benchmarks...")

for n in SIZES:
    for d in DIMENSIONS:
        print(f"Testando N={n}, D={d}...")
        
        # Gerar dados
        X, y = make_blobs(n_samples=n, n_features=d, centers=5, random_state=42)
        
        # Iniciar medição
        tracemalloc.start()
        start_time = time.time()
        
        # Executar HDBSCAN (Baseline)
        clusterer = HDBSCAN(min_cluster_size=15, metric='euclidean')
        clusterer.fit(X)
        
        # Parar medição
        end_time = time.time()
        current, peak = tracemalloc.get_traced_memory()
        tracemalloc.stop()
        
        # Registrar
        RESULTS.append({
            'Algorithm': 'HDBSCAN_Standard',
            'N': n,
            'D': d,
            'Time_Sec': end_time - start_time,
            'Memory_MB': peak / 10**6
        })

# Salvar
df = pd.DataFrame(RESULTS)
df.to_csv('benchmark_results_baseline.csv', index=False)
print("Resultados salvos!")
