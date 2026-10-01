# Installation and quick start

MustaCHE 0.3.0 and CORE-SG 0.4.5 are stable packages on **TestPyPI**. They
have not yet been published to official PyPI. The qualified combination is
CPython 3.11 on Windows x86-64 or Linux x86-64 (glibc >= 2.28). macOS and
other Python versions are not qualified for this release.

## Windows (PowerShell)

```powershell
py -3.11 -m venv .venv
.\.venv\Scripts\python.exe -m pip install --extra-index-url https://test.pypi.org/simple/ mustache-core==0.3.0
.\.venv\Scripts\python.exe -m pip check
.\.venv\Scripts\mustache.exe
```

## Linux

```bash
python3.11 -m venv .venv
.venv/bin/python -m pip install --extra-index-url https://test.pypi.org/simple/ mustache-core==0.3.0
.venv/bin/python -m pip check
.venv/bin/mustache
```

Open <http://127.0.0.1:5000> and choose **Datasets**. For a short example,
select **Iris**, keep **CORE-SG**, set Minimum mpts to 2, Maximum mpts to 6,
Step size to 2, and Distance metric to Manhattan. Run Batch, inspect the HAI
Similarity Matrix and Meta-Hierarchy Dendrogram, then select a visible branch
node. Save Analysis, reopen it from Projects & History, and export CSV or ZIP.

The package metadata installs `core-sg-mustache==0.4.5`, `hdbscan==0.8.44`
and the remaining runtime dependencies. `--extra-index-url` is a convenience:
it permits both official PyPI and TestPyPI to supply dependencies. The
[strict reproduction procedure](reproducao.md) obtains the two named packages
from TestPyPI separately and resolves their dependencies through official PyPI.
Do not interpret this command as an official-PyPI installation command.

You can also start the application with `python -m mustache.cli`. The server
is a local, single-user research application, not a hosted multi-user service.
