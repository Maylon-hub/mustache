"""
test_cython_backend.py — Verifica se o backend Cython do core-sg está ativo.
Uso: python test_cython_backend.py
"""
import sys
import os
import warnings

CORE_SG_PATH = r"C:\Users\guest\Documents\GitHub\core-sg"
if CORE_SG_PATH not in sys.path:
    sys.path.insert(0, CORE_SG_PATH)

ok = True

print("=== Teste do Backend Cython do core-sg ===")

try:
    from core_sg._reweight import reweight_core_sg_from_lookup
    print("  [OK] _reweight (Cython backend) importado")
except ImportError as e:
    print(f"  [FAIL] _reweight: {e}")
    ok = False

try:
    from core_sg._mst_kruskal import kruskal_mst_impl
    print("  [OK] _mst_kruskal (Cython backend) importado")
except ImportError as e:
    print(f"  [FAIL] _mst_kruskal: {e}")
    ok = False

# Teste funcional
try:
    from sklearn.datasets import make_blobs
    from core_sg import CoreSG

    X, _ = make_blobs(n_samples=200, n_features=3, centers=4, random_state=42)
    core = CoreSG(metric="euclidean", p=2)

    with warnings.catch_warnings():
        warnings.simplefilter("error", RuntimeWarning)
        core.fit(X, k_max=10)

    mst = core.extract_mst_from_core_sg(k=5)
    print(f"  [OK] CoreSG.fit + extract_mst -> {len(mst)} arestas no MST")

except RuntimeWarning as w:
    print(f"  [WARN] Ainda usando Python fallback: {w}")
    ok = False
except Exception as e:
    print(f"  [FAIL] Erro funcional: {e}")
    ok = False

print("")
if ok:
    print("Resultado: BACKEND CYTHON ATIVO")
    sys.exit(0)
else:
    print("Resultado: FALLBACK PYTHON (backend Cython nao disponivel)")
    sys.exit(1)
