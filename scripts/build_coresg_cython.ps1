# build_coresg_cython.ps1
# Build core-sg Cython extensions on Windows with MSVC.
# Run from the MustaCHE repository root:
#   .\scripts\build_coresg_cython.ps1
#
# Requirements:
#   - Visual Studio Build Tools 2022+ with MSVC v143
#   - Python environment with cython >= 3.0 and numpy installed
# Optional legacy helper: check the paths below before running. It writes
# setup_cython.py in the CORE-SG checkout; prefer the normal pip source build.

$ErrorActionPreference = "Stop"

$CORE_SG_DIR  = "C:\Users\guest\Documents\GitHub\core-sg"
$PYTHON_EXE   = "C:\Users\guest\Documents\GitHub\mustache\venv\Scripts\python.exe"
$VCVARS64     = "C:\Program Files (x86)\Microsoft Visual Studio\18\BuildTools\VC\Auxiliary\Build\vcvars64.bat"

# --- Auto-detect vcvars64 se o caminho padrão não existir ---
if (-not (Test-Path $VCVARS64)) {
    $found = Get-ChildItem "C:\Program Files (x86)\Microsoft Visual Studio" `
        -Recurse -Filter "vcvars64.bat" -ErrorAction SilentlyContinue |
        Select-Object -First 1
    if ($found) { $VCVARS64 = $found.FullName }
    else {
        Write-Error "vcvars64.bat was not found. Install Visual Studio Build Tools."
        exit 1
    }
}

Write-Host "=== Core-SG Cython Build (Windows/MSVC) ===" -ForegroundColor Cyan
Write-Host "  core-sg dir : $CORE_SG_DIR"
Write-Host "  Python      : $PYTHON_EXE"
Write-Host "  vcvars64    : $VCVARS64"
Write-Host ""

# --- Criar setup_cython.py temporário no diretório core-sg ---
$setupScript = @'
"""
Minimal setup script for building only the core-sg Cython extensions.
Does not modify the original pyproject.toml.
"""
from setuptools import setup, Extension
from Cython.Build import cythonize
import numpy as np

extensions = [
    Extension(
        "core_sg._mst_kruskal",
        sources=["core_sg/_mst_kruskal.pyx"],
        include_dirs=[np.get_include()],
        define_macros=[("NPY_NO_DEPRECATED_API", "NPY_1_7_API_VERSION")],
    ),
    Extension(
        "core_sg._reweight",
        sources=["core_sg/_reweight.pyx"],
        include_dirs=[np.get_include()],
        define_macros=[("NPY_NO_DEPRECATED_API", "NPY_1_7_API_VERSION")],
    ),
]

setup(
    name="core_sg_ext",
    ext_modules=cythonize(
        extensions,
        compiler_directives={
            "language_level": "3",
            "boundscheck": False,
            "wraparound": False,
            "cdivision": True,
        },
        annotate=False,
    ),
)
'@

$setupPath = Join-Path $CORE_SG_DIR "setup_cython.py"
Set-Content -Path $setupPath -Value $setupScript -Encoding UTF8
Write-Host "setup_cython.py created at: $setupPath" -ForegroundColor Green

# --- Criar .cmd que ativa MSVC e roda o build ---
$cmdScript = @"
@echo off
call "$VCVARS64"
if %errorlevel% neq 0 (
    echo ERROR: Failed to configure the MSVC environment
    exit /b 1
)
cd /d "$CORE_SG_DIR"
"$PYTHON_EXE" setup_cython.py build_ext --inplace
exit /b %errorlevel%
"@

$tmpCmd = "$env:TEMP\build_core_sg.cmd"
Set-Content -Path $tmpCmd -Value $cmdScript -Encoding ASCII

Write-Host "Building Cython extensions..." -ForegroundColor Yellow
cmd /c $tmpCmd
$buildResult = $LASTEXITCODE

if ($buildResult -ne 0) {
    Write-Host ""
    Write-Error "Build failed with code $buildResult. Check the errors above."
    exit $buildResult
}

# --- Verificar .pyd gerados ---
Write-Host ""
Write-Host "=== Compiled modules ===" -ForegroundColor Cyan
$pyds = Get-ChildItem -Path (Join-Path $CORE_SG_DIR "core_sg") -Filter "*.pyd"
if ($pyds) {
    foreach ($pyd in $pyds) {
        Write-Host "  ✓ $($pyd.Name)" -ForegroundColor Green
    }
} else {
    Write-Warning "No .pyd files were found after the build!"
}

# --- Teste de importação ---
Write-Host ""
Write-Host "=== Testing Cython imports ===" -ForegroundColor Cyan
$testCode = @'
import sys, os
sys.path.insert(0, r"C:\Users\guest\Documents\GitHub\core-sg")
import warnings

ok = True

try:
    from core_sg._reweight import reweight_core_sg_from_lookup
    print("  OK  _reweight  (Cython backend)")
except ImportError as e:
    print(f"  FAIL _reweight: {e}")
    ok = False

try:
    from core_sg._mst_kruskal import kruskal_mst_impl
    print("  OK  _mst_kruskal (Cython backend)")
except ImportError as e:
    print(f"  FAIL _mst_kruskal: {e}")
    ok = False

# Teste funcional rápido
try:
    from sklearn.datasets import make_blobs
    from core_sg import CoreSG
    X, _ = make_blobs(n_samples=200, n_features=3, centers=4, random_state=42)
    core = CoreSG(metric="euclidean", p=2)
    with warnings.catch_warnings():
        warnings.simplefilter("error", RuntimeWarning)
        core.fit(X, k_max=10)
    mst = core.extract_mst_from_core_sg(k=5)
    print(f"  OK  CoreSG.fit + extract_mst ({len(mst)} MST edges)")
except RuntimeWarning as w:
    print(f"  WARN functional check: still using the Python fallback — {w}")
    ok = False
except Exception as e:
    print(f"  FAIL functional check: {e}")
    ok = False

sys.exit(0 if ok else 1)
'@

& $PYTHON_EXE -c $testCode
$testResult = $LASTEXITCODE

Write-Host ""
if ($testResult -eq 0) {
    Write-Host "=== BUILD AND TESTS: SUCCESS ✓ ===" -ForegroundColor Green
    Write-Host "core-sg is using the compiled Cython backend." -ForegroundColor Green
} else {
    Write-Host "=== BUILD OK, but imports failed ✗ ===" -ForegroundColor Red
    Write-Host "Check that MustaCHE's sys.path points to $CORE_SG_DIR" -ForegroundColor Yellow
}
