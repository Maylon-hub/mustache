import numpy as np
from sklearn.cluster import HDBSCAN
from scipy.spatial.distance import pdist, squareform
from scipy.cluster.hierarchy import leaves_list, to_tree, linkage

def build_distance_matrix(Z, n_samples):
    """
    Constructs the hierarchy distance matrix from the linkage matrix Z.
    D[i, j] = Size of the smallest cluster containing both i and j, normalized by n_samples.
    Z structure: [idx1, idx2, distance, sample_count]
    """
    D = np.zeros((n_samples, n_samples))
    
    # We need to track the members of each cluster.
    # Initial clusters are just the points themselves: 0..(n-1)
    cluster_members = {i: [i] for i in range(n_samples)}
    
    # Iterate through Z
    for i, row in enumerate(Z):
        # Index of the new cluster being formed
        new_cluster_idx = n_samples + i
        
        child1_idx = int(row[0])
        child2_idx = int(row[1])
        # row[3] is number of samples in the new cluster (size)
        cluster_size = row[3]
        
        normalized_size = cluster_size / n_samples
        
        members1 = cluster_members[child1_idx]
        members2 = cluster_members[child2_idx]
        
        # Fill D for all pairs between members1 and members2
        m1 = np.array(members1)
        m2 = np.array(members2)
        
        D[np.ix_(m1, m2)] = normalized_size
        D[np.ix_(m2, m1)] = normalized_size
        
        # Merge members for the new cluster
        cluster_members[new_cluster_idx] = members1 + members2
        
        # Cleanup old keys to free memory
        del cluster_members[child1_idx]
        del cluster_members[child2_idx]
        
    # Set diagonal to 1/n (size of single point cluster)
    np.fill_diagonal(D, 1.0 / n_samples)
        
    return D

def compute_hai_score(D1, D2):
    """
    Computes HAI between two distance matrices.
    HAI = 1 - (total_diff / n^2)
    """
    n = D1.shape[0]
    diff = np.abs(D1 - D2)
    total_diff = np.sum(diff)
    return 1.0 - (total_diff / (n * n))


def compute_hai_matrix(linkage_list, n_samples):
    """
    Computes the HAI matrix for a list of linkage structures.
    """
    n_hierarchies = len(linkage_list)
    hai_matrix = np.zeros((n_hierarchies, n_hierarchies))
    
    d_matrices = [build_distance_matrix(Z, n_samples) for Z in linkage_list]
    
    for i in range(n_hierarchies):
        for j in range(i, n_hierarchies):
            if i == j:
                score = 1.0
            else:
                score = compute_hai_score(d_matrices[i], d_matrices[j])
            
            hai_matrix[i, j] = score
            hai_matrix[j, i] = score
            
    return hai_matrix

def run_meta_clustering(hai_matrix):
    """
    Runs HDBSCAN on the HAI matrix (converted to distance).
    Returns labels and a linkage matrix (manually computed via scipy).
    """
    distance_matrix = 1.0 - hai_matrix
    distance_matrix[distance_matrix < 0] = 0
    np.fill_diagonal(distance_matrix, 0)
    
    # Run HDBSCAN for labels (using sklearn version)
    clusterer = HDBSCAN(metric='precomputed', min_cluster_size=2, allow_single_cluster=True)
    clusterer.fit(distance_matrix)
    labels = clusterer.labels_
    
    # Generate Linkage Matrix for Dendrogram using scipy (Hybrid Approach)
    # This replaces the missing single_linkage_tree_ attribute in sklearn 1.3
    condensed_dist = squareform(distance_matrix)
    linkage_matrix = linkage(condensed_dist, method='single')
    
    return labels.tolist(), linkage_matrix.tolist()


def compute_medoids(hai_matrix, labels):
    """
    Identifies the medoid for each meta-cluster.
    """
    distance_matrix = 1.0 - hai_matrix
    unique_labels = np.unique(labels)
    medoids = {}
    
    for label in unique_labels:
        if label == -1:
            continue
            
        indices = np.where(np.array(labels) == label)[0]
        if len(indices) == 0:
            continue
            
        sub_matrix = distance_matrix[np.ix_(indices, indices)]
        total_distances = np.sum(sub_matrix, axis=0)
        min_idx = np.argmin(total_distances)
        medoids[int(label)] = int(indices[min_idx])
        
    return medoids
