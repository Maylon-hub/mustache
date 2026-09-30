# Qualified environment records

`build-win-py311.txt` and `runtime-win-py311.txt` freeze the concrete Windows
CPython 3.11 qualification environments. They are not universal cross-platform
locks. Use a fresh venv, install from these records, build both projects, then
install their artifacts. Archive dependency wheels and SHA-256s alongside the
four project artifacts for offline replay. No editable install or PYTHONPATH.
Project metadata defines supported dependency resolution; these records define
the one actually exercised combination. Requalify before widening native
HDBSCAN beyond 0.8.44. Build-tool versions alone do not ensure bit-identical
native binaries across compilers/operating systems.
