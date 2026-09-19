filePath = r"C:\Users\guest\Documents\GitHub\core-sg\core_sg\core_sg.py"
with open(filePath, 'r', encoding='utf-8') as f:
    content = f.read()

old_hdb = """        clusterer = hdbscan.HDBSCAN(
            min_cluster_size=k_max,
            min_samples=k_max,
            metric="euclidean",
            core_dist_n_jobs=1,
        )"""

new_hdb = """        clusterer = hdbscan.HDBSCAN(
            min_cluster_size=k_max,
            min_samples=k_max,
            metric="euclidean",
            core_dist_n_jobs=1,
            gen_min_span_tree=True,
            approx_min_span_tree=False,
        )"""

assert old_hdb in content, "old_hdb not found"
content = content.replace(old_hdb, new_hdb)

with open(filePath, 'w', encoding='utf-8') as f:
    f.write(content)

print("Successfully fixed gen_min_span_tree in core_sg.py!")