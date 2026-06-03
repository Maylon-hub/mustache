import pandas as pd
import sys
import os
import json

sys.path.insert(0, os.getcwd())
from mustache.core.batch import run_batch_clustering

df = pd.read_csv('datasets/100-amostras.csv')
batch_results = run_batch_clustering(df, 11, 15, 2, metric='euclidean', algorithm='core-sg')

# Dump reachability_json for mpts=11
res = batch_results['11']
with open('scratch/reachability_mpts_11.json', 'w') as f:
    f.write(res['reachability_json'])

print("Dumped reachability_json to scratch/reachability_mpts_11.json")
