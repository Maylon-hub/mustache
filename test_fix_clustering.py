import numpy as np
import pandas as pd
from app.core.clustering import compute_mutual_reachability
from scipy.spatial.distance import squareform, is_valid_dm

def test_mr():
    print("Testing MR calculation...")
    data = np.random.rand(10, 2)
    min_samples = 3
    
    mr = compute_mutual_reachability(data, min_samples)
    print(f"MR Matrix shape: {mr.shape}")
    print(f"Diagonal max: {np.max(np.abs(np.diag(mr)))}")
    print(f"Symmetry check (max diff): {np.max(np.abs(mr - mr.T))}")
    
    # Check manual validity
    if not np.allclose(np.diag(mr), 0):
        print("FAIL: Diagonal not zero")
    if not np.allclose(mr, mr.T):
        print("FAIL: Not symmetric")
        
    try:
        condensed = squareform(mr)
        print("Success: squareform conversion worked.")
    except Exception as e:
        print(f"FAIL: squareform failed: {e}")
        # Print diagonal if failed
        print("Diagonal elements:", np.diag(mr))
        
    # Check is_valid_dm explicit
    valid = is_valid_dm(mr, tol=1e-8, throw=True, name="MR")
    print(f"is_valid_dm returned: {valid}")

if __name__ == "__main__":
    test_mr()
