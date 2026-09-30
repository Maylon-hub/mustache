# Reproduction of the current MustaCHE source

This procedure targets the corrected source, not historical benchmark results
or a previously published wheel. Record both Git commit IDs and any uncommitted
patches before describing a run as reproducible.

## Install both development repositories

Use CPython 3.11, Git and a compiler for a source build of CORE-SG. Commands
below are PowerShell and do not require activating scripts:

```powershell
git clone --branch mustache-core-sg https://github.com/Maylon-hub/mustache.git
git clone --branch develop https://github.com/Maylon-hub/core-sg.git
cd mustache
python -m venv .venv
.\.venv\Scripts\python.exe -m pip install --upgrade pip
.\.venv\Scripts\python.exe -m pip install -e ../core-sg
.\.venv\Scripts\python.exe -m pip install -e ".[dev]"
.\.venv\Scripts\python.exe -m pip check
git rev-parse HEAD
git -C ../core-sg rev-parse HEAD
git diff
git -C ../core-sg diff
.\.venv\Scripts\python.exe -m pip freeze
```

Use `.venv/bin/python` on Linux. Do not copy an existing environment
between machines. Keep the pip freeze output with the experiment record.

The official RC scope is Windows/Linux x86-64 with CPython 3.11. Linux results
must be recorded from the artifact qualification workflow; configuration alone
does not establish a pass. macOS is not currently qualified and remains future
work. Other Python versions are not advertised by this RC.

## Verify what is actually imported

```powershell
.\.venv\Scripts\python.exe -c "import mustache, core_sg; print(mustache.__file__); print(core_sg.__file__)"
.\.venv\Scripts\python.exe -m mustache.cli --help
.\.venv\Scripts\python.exe -m pytest -q
```

Distribution metadata can be stale when PYTHONPATH points at a different source
checkout. Inspect import paths as well as package versions. The technical-review
tests compare known HAI values and the public unrounded CORE-SG path against
reference HDBSCAN for multiple metrics and neighborhood settings.

For the backend suite, from the CORE-SG checkout:

```powershell
..\mustache\.venv\Scripts\python.exe -m pytest -q
```

On restricted Windows execution environments, Joblib may fail to create named
pipes and Numba may fail to write its cache. Record those environmental failures
and rerun the affected tests in an environment that permits the required
operations. Disabling JIT changes the test environment and must be disclosed.

## Reproduce the API example and the interface

Run the code in the [user guide](guia_documentacao.md), then execute every cell
of `examples/mustache_quickstart.ipynb` in the same environment.

```powershell
.\.venv\Scripts\python.exe -m mustache.cli --host 127.0.0.1 --port 5000
```

In the browser:

1. Open Datasets and configure Iris, CORE-SG, mpts 2..6, step 2, Manhattan.
2. Verify the sidebar parameters, three ordered HAI entries, dendrogram and
   representative hierarchy descriptions.
3. Switch to distance-threshold mode and adjust the line. Then select a branch
   to create a manual meta-cluster; verify that the mode and medoid update.
4. Save, reopen the project and verify that parameters, active representatives,
   manual groups and mode are unchanged. Threshold state is retained for
   returning to threshold mode, not displayed as the active manual partition.
5. Export the selected labels and verify the dataset sample count.
6. Optionally repeat with the HDBSCAN comparison baseline on the same input,
   range and metric. Record any differences rather than assuming universal parity.

The maintained review check is `scripts/verify_web_ui.cjs`. It requires Node.js,
Playwright and installed Google Chrome. The older Selenium script remains for
compatibility but was not used in this review. Launch a separate test server
with isolated project storage so browser-created projects do not affect your
research records:

```powershell
$env:MUSTACHE_PROJECTS_DIR = Join-Path $env:TEMP ('mustache-ui-' + [guid]::NewGuid())
.\.venv\Scripts\python.exe -m mustache.cli --host 127.0.0.1 --port 5057
```

In another terminal with Playwright available:

```powershell
node scripts/verify_web_ui.cjs http://127.0.0.1:5057 ./ui-review
# Optional baseline regression check:
node scripts/verify_web_ui.cjs http://127.0.0.1:5057 ./ui-baseline-review hdbscan
```

The default check uses CORE-SG. It checks save/reopen/export, manual representatives, metadata, assets and
basic mobile overflow, and records JSON plus screenshots. Its Plotly event
checks are not physical hit-testing. Use `scripts/verify_manual_dendrogram.py`
for the separate real-pointer Chrome regression.

## Candidate packages instead of source

The unpublished stable-candidate pair is `mustache-core==0.3.0` and
`core-sg-mustache==0.4.5`. Qualify their newly built artifacts using the
artifact-only approach in [RC preparation](rc_preparation.md); that page is a
historical RC procedure. Do not use an editable install or PYTHONPATH to
qualify package installation. The previously qualified RCs remain on TestPyPI;
to reproduce that historical pair, install normal dependencies from PyPI and
the two explicit RC packages with `--no-deps`:

```powershell
python -m pip install Flask numpy pandas scikit-learn scipy plotly hdbscan==0.8.44 pynndescent
# Historical TestPyPI RCs, not the unpublished stable artifacts:
python -m pip install --index-url https://test.pypi.org/simple/ --no-deps core-sg-mustache==0.4.5rc3 mustache-core==0.3.0rc3
python -m pip check
```

Verify wheel availability for the actual Python/platform combination. The
stable pair must be installed from its own freshly built wheel/sdist until
separately authorized for publication. These commands do not qualify it.

## Benchmarks and scientific acceptance

Existing benchmark scripts include
`scripts/benchmark_coresg_vs_hdbscan.py` and
`scripts/benchmark_coresg_vs_hdbscan_canonical.py`.
Their archived numbers predate correctness fixes. The updated scripts write to
new experiment directories, not the archived documentation reports. To smoke
test the scripts with bounded data and separate output directories:

```powershell
.\.venv\Scripts\python.exe scripts/benchmark_coresg_vs_hdbscan.py --quick --output-dir ./benchmark-smoke
.\.venv\Scripts\python.exe scripts/benchmark_coresg_vs_hdbscan_canonical.py --quick --output-dir ./benchmark-canonical-smoke
```

These scripts still time unequal extraction versus complete fitting workloads;
their ratios are not end-to-end MustaCHE speedups. The Windows Cython build
helper is optional and was not executed during this review; source installation
uses CORE-SG's packaging configuration.

Do not cite their old timings as current performance or as equivalence to the
Java/RNG implementation. A valid new comparison must use the same dataset,
metric, density convention and output workload, include support construction
and HAI/visualization costs where claimed, and retain per-run raw timings,
seeds, dependency versions and hardware. No nonexistent checksums, scripts or
bit-for-bit cross-platform guarantees are promised here.
