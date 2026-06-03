import pandas as pd
import sys
import os
import numpy as np

sys.path.insert(0, os.getcwd())
from mustache.core.clustering import run_clustering

df = pd.read_csv('datasets/100-amostras.csv')
res = run_clustering(df, min_cluster_size=17, min_samples=17, algorithm='core-sg')

# Let's inspect what happens inside run_clustering
# We can do this by running the OPTICS code block directly
from sklearn.cluster import OPTICS
data = df.select_dtypes(include=[np.number]).to_numpy()
optics = OPTICS(min_samples=17, metric='euclidean')
optics.fit(data)

reachability = optics.reachability_[optics.ordering_]
print("reachability (ordered by optics):", reachability[:20])
print("Is reachability (ordered by optics) sorted?", np.all(np.diff(reachability[np.isfinite(reachability)]) >= 0))

# Wait, is there any OTHER reachability plot or does the frontend sort it?
# Let's check main.js to see if it does any sorting or if something else is going on!
