"""Diagnose meta-dendrogram issues in batch analysis."""
import sys, os, json
import numpy as np
sys.path.insert(0, os.getcwd())

from mustache.core.hai import run_meta_clustering, compute_hai_matrix

# Simulate a small case with 10 hierarchies using synthetic linkage matrices
# In 500-amostras dataset with mpts 2..50 step 5 => 10 hierarchies
n_samples = 500
n_hier = 10

# Create a random set of linkage matrices (N-1 merges each)
rng = np.random.default_rng(42)

linkage_list = []
for _ in range(n_hier):
    # Generate a valid random linkage for n_samples
    from scipy.cluster.hierarchy import linkage as sp_linkage
    data = rng.normal(size=(n_samples, 5))
    Z = sp_linkage(data, method='single')
    linkage_list.append(Z)

print(f"Computing HAI matrix for {n_hier} hierarchies of {n_samples} samples...")
hai_matrix = compute_hai_matrix(linkage_list, n_samples)
print(f"HAI range: {hai_matrix.min():.4f} - {hai_matrix.max():.4f}")
print(f"HAI diagonal: {np.diag(hai_matrix)}")

meta_labels, meta_linkage = run_meta_clustering(hai_matrix)
meta_linkage = np.array(meta_linkage)
print(f"meta_linkage shape: {meta_linkage.shape}")
print(f"meta_linkage:\n{meta_linkage}")
print(f"meta_labels: {meta_labels}")
print(f"distance range in meta_linkage: {meta_linkage[:, 2].min():.6f} - {meta_linkage[:, 2].max():.6f}")

# Now try ff.create_dendrogram approach
import plotly.figure_factory as ff
sorted_keys = [str(2 + i*5) for i in range(n_hier)]
dendro_labels = sorted_keys
get_z = lambda x: meta_linkage
dummy_X = np.zeros((len(sorted_keys), 1))

try:
    fig = ff.create_dendrogram(dummy_X, linkagefun=get_z, labels=dendro_labels)
    fig_data = json.loads(fig.to_json())
    print(f"\nff.create_dendrogram traces: {len(fig_data['data'])}")
    for i, t in enumerate(fig_data['data'][:5]):
        y = t.get('y', [])
        x = t.get('x', [])
        print(f"  trace[{i}]: len(x)={len(x) if y else '?'} len(y)={len(y) if isinstance(y, list) else type(y)} y_max={max(y) if isinstance(y, list) and y else 'N/A'}")
    xaxis = fig_data['layout'].get('xaxis', {})
    print(f"  xaxis tickvals: {xaxis.get('tickvals')}")
    print(f"  xaxis ticktext: {xaxis.get('ticktext')}")
except Exception as e:
    print(f"ff.create_dendrogram error: {e}")

print("\n--- Testing scipy dendrogram approach ---")
from scipy.cluster.hierarchy import dendrogram as sp_dendrogram
ddict = sp_dendrogram(meta_linkage, labels=dendro_labels, no_plot=True)
print(f"icoord shape: {np.array(ddict['icoord']).shape}")
print(f"dcoord shape: {np.array(ddict['dcoord']).shape}")
print(f"ivl (leaf labels): {ddict['ivl']}")
print(f"dcoord range: {np.array(ddict['dcoord']).min():.6f} - {np.array(ddict['dcoord']).max():.6f}")
