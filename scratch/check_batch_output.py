import pandas as pd
import numpy as np
import sys
import os
import json

sys.path.insert(0, os.getcwd())
from mustache.core.batch import run_batch_clustering, analyze_batch_results

df = pd.read_csv('datasets/100-amostras.csv')
batch_results = run_batch_clustering(df, 11, 20, 3, metric='euclidean', algorithm='core-sg')
analysis = analyze_batch_results(batch_results)

# Let's inspect the reachability_json for mpts=17
mpts_val = '17'
res = batch_results[mpts_val]
fig_reach = json.loads(res['reachability_json'])

y_vals = fig_reach['data'][0]['y']
x_vals = fig_reach['data'][0]['x']

print(f"For mpts={mpts_val}:")
print("x length:", len(x_vals))
print("y length:", len(y_vals))
print("First 10 y_vals:", y_vals[:10])
print("Is y_vals sorted?", all(y_vals[i] <= y_vals[i+1] for i in range(len(y_vals)-1)))

# Let's check if there is any other trace or if something else is in fig_reach
print("Data traces count:", len(fig_reach['data']))
print("First trace type:", fig_reach['data'][0]['type'])
print("First trace name:", fig_reach['data'][0].get('name'))
