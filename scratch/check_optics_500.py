import pandas as pd
import numpy as np
from sklearn.cluster import OPTICS

df = pd.read_csv('datasets/500-amostras.csv')
data = df.select_dtypes(include=[np.number]).to_numpy()

optics = OPTICS(min_samples=17, metric='euclidean')
optics.fit(data)

reachability = optics.reachability_[optics.ordering_]
print("reachability shape:", reachability.shape)
print("Finite reachability values (first 20):", reachability[np.isfinite(reachability)][:20])
print("Is reachability sorted?", np.all(np.diff(reachability[np.isfinite(reachability)]) >= 0))
