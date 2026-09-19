import pandas as pd
import numpy as np
from sklearn.cluster import OPTICS

df = pd.read_csv('datasets/100-amostras.csv')
data = df.select_dtypes(include=[np.number]).to_numpy()

optics = OPTICS(min_samples=5, metric='euclidean')
optics.fit(data)

reachability = optics.reachability_[optics.ordering_]
print("Reachability shape:", reachability.shape)
print("First 20 reachability values:", reachability[:20])
print("Max reachability:", np.max(reachability))
print("Min reachability:", np.min(reachability))
print("Finite reachability values:", reachability[np.isfinite(reachability)][:20])
print("Is reachability sorted?", np.all(np.diff(reachability[np.isfinite(reachability)]) >= 0))
