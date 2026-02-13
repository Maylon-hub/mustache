import pandas as pd
import numpy as np
import sys
import os

sys.path.append(os.getcwd())
from app.core.clustering import run_clustering

print("Testing simple clustering...")
df = pd.DataFrame([[1,1], [1,2], [10,10], [10,11]], columns=['x', 'y'])
try:
    res = run_clustering(df, min_cluster_size=2)
    print(f"Success! clusters: {res['n_clusters']}")
except Exception as e:
    print(f"Error: {e}")
