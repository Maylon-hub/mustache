# Reproduction of MustaCHE 0.3.0

The stable MustaCHE 0.3.0 and CORE-SG 0.4.5 packages are published on TestPyPI.
This page separates artifact-based reproduction from source development. Record
the installed versions, wheel hashes and environment with each experiment.

## Stable packages with isolated package sources

Use a new CPython 3.11 environment outside both checkouts. On Windows
(PowerShell), download only the two named stable wheels from TestPyPI, then
install those local wheels with dependencies resolved from official PyPI:

```powershell
py -3.11 -m venv .venv
$python = (Resolve-Path .\.venv\Scripts\python.exe).Path
& $python -m pip install --upgrade pip
New-Item -ItemType Directory -Force .\testpypi-wheels | Out-Null
& $python -m pip download --only-binary=:all: --no-deps --index-url https://test.pypi.org/simple/ --dest .\testpypi-wheels core-sg-mustache==0.4.5 mustache-core==0.3.0
$wheels = @(Get-ChildItem .\testpypi-wheels\*.whl)
if ($wheels.Count -ne 2) { throw 'Expected exactly two TestPyPI wheels.' }
$wheels | Get-FileHash -Algorithm SHA256
& $python -m pip install $wheels.FullName
& $python -m pip check
& $python -c "from importlib.metadata import version; import mustache, core_sg; print(version('mustache-core'), mustache.__file__); print(version('core-sg-mustache'), core_sg.__file__)"
```

Compare wheel hashes with the qualified-artifact records for the target OS;
the Windows CORE-SG 0.4.5 wheel SHA-256 is
`cdf726336d073103c1911e6e0d651c73a793ec0d824016e09386c4f2f0fdb9fd` and the
MustaCHE 0.3.0 universal wheel SHA-256 is
`5fbca8c6751c8d06671278064f9678d085e159eaba97857ae5cd639b72696166`.
The qualified Linux CORE-SG wheel SHA-256 is
`ca5117f88f1322b2efc6ee7ef34923dd5aa944d2ed084613f903239097b50032`.
Do not substitute a source checkout using `PYTHONPATH` when qualifying installed
artifacts. A simpler but less index-isolated command is on
[Installation](installation.md).

## Source development

Use CPython 3.11, Git and a compiler for a source build of CORE-SG. Commands
below are PowerShell and do not require activating scripts:

```powershell
git clone --branch master https://github.com/Maylon-hub/mustache.git
git clone --branch main https://github.com/Maylon-hub/core-sg.git
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

The stable scope is Windows/Linux x86-64 with CPython 3.11; both platforms
passed artifact qualification. macOS remains unqualified/future work, not
declared incompatible. Other Python versions are not advertised as qualified.

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

The maintained browser checks use Playwright and real Chrome. The general
`scripts/verify_web_ui.cjs` check includes programmatic Plotly-event checks;
these do **not** establish physical hit-testing. The separate
`scripts/verify_manual_dendrogram.py` uses real pointer clicks and verifies
manual selection, persistence and export. Launch a separate test server
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

The [historical RC procedure](rc_preparation.md) records preparation of the
earlier `rc3` pair. It is not the stable installation path.

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
