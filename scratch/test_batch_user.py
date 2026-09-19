import pandas as pd
import sys
import os

sys.path.append(os.getcwd())
from mustache.core.batch import run_batch_clustering, analyze_batch_results
from mustache.core.clustering import run_clustering

print("=== Simulating User's Batch Run ===")
df = pd.read_csv("datasets/simple_2d.csv")
print(f"Loaded DataFrame with shape: {df.shape}")

results = {}
for mpts in range(2, 51, 2):
    try:
        res = run_clustering(df, min_cluster_size=mpts, min_samples=mpts, metric='euclidean', algorithm='core-sg')
        results[str(mpts)] = res
        print(f"mpts={mpts}: SUCCESS")
    except Exception as e:
        print(f"mpts={mpts}: FAIL - {type(e).__name__}: {str(e)}")

print("\nRunning meta-analysis...")
try:
    analysis = analyze_batch_results(results)
    if 'error' in analysis:
        print(f"Analysis returned expected soft error: {analysis['error']}")
    else:
        print("Analysis succeeded!")
        print("meta_labels:", analysis.get('meta_labels'))
        print("medoids:", analysis.get('medoids'))
        print("ordered_mpts:", analysis.get('ordered_mpts'))
except Exception as e:
    print(f"Analysis failed with unexpected exception: {e}")
