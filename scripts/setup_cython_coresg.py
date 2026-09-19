"""
setup_cython.py — Compila as extensoes Cython do core-sg.
USA distutils.core.setup (nao setuptools) para evitar a leitura/validacao
do pyproject.toml do core-sg, que usa formato de license incompativel
com setuptools >= 77.

Uso: python setup_cython.py build_ext --inplace
"""
# Usar distutils diretamente para ignorar pyproject.toml
from distutils.core import setup, Extension
from Cython.Build import cythonize
import numpy as np
import os
import sys

# Garantir que nao tentamos ler pyproject.toml do diretorio atual
os.environ["SETUPTOOLS_USE_DISTUTILS"] = "local"

extensions = [
    Extension(
        "core_sg._mst_kruskal",
        sources=["core_sg/_mst_kruskal.pyx"],
        include_dirs=[np.get_include()],
        define_macros=[("NPY_NO_DEPRECATED_API", "NPY_1_7_API_VERSION")],
        extra_compile_args=["/O2"] if sys.platform == "win32" else ["-O3"],
    ),
    Extension(
        "core_sg._reweight",
        sources=["core_sg/_reweight.pyx"],
        include_dirs=[np.get_include()],
        define_macros=[("NPY_NO_DEPRECATED_API", "NPY_1_7_API_VERSION")],
        extra_compile_args=["/O2"] if sys.platform == "win32" else ["-O3"],
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
