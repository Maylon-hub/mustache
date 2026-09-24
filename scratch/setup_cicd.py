import os

def main():
    # 1. Update pyproject.toml in core-sg
    pyproject_path = r'C:\Users\guest\Documents\GitHub\core-sg\pyproject.toml'
    with open(pyproject_path, 'r', encoding='utf-8') as f:
        content = f.read()

    content = content.replace('version = "0.3.0"', 'version = "0.4.0"')
    
    cibw_old = '''[tool.cibuildwheel]
build = ["cp310-*", "cp311-*", "cp312-*", "cp313-*"]
skip = ["*-musllinux_*", "*-manylinux_i686", "pp*"]

archs = ["x86_64"]'''

    cibw_new = '''[tool.cibuildwheel]
build = "cp310-* cp311-* cp312-* cp313-* cp314-*"
skip = ["*-musllinux_*", "*-manylinux_i686", "pp*"]
test-command = "python -c \\"from sklearn.datasets import make_blobs; from core_sg import CoreSG; X, _ = make_blobs(n_samples=120, n_features=3, centers=3, random_state=42); core = CoreSG(metric='euclidean', p=2); core.fit(X, k_max=5); mst = core.extract_mst_from_core_sg(k=3); assert mst is not None\\""

[tool.cibuildwheel.macos]
archs = ["x86_64", "arm64"]

[tool.cibuildwheel.windows]
archs = ["AMD64"]

[tool.cibuildwheel.linux]
manylinux-x86_64-image = "manylinux2014"'''

    if cibw_old in content:
        content = content.replace(cibw_old, cibw_new)
        print("Replaced tool.cibuildwheel successfully.")
    else:
        print("Warning: cibw_old string not found exactly, doing custom replacement.")
        lines = content.splitlines()
        new_lines = []
        in_cibw = False
        for line in lines:
            if line.strip() == "[tool.cibuildwheel]":
                in_cibw = True
                new_lines.append(cibw_new)
                continue
            if in_cibw and line.startswith("[") and not line.startswith("[tool.cibuildwheel"):
                in_cibw = False
            if not in_cibw:
                new_lines.append(line)
        content = "\n".join(new_lines)

    with open(pyproject_path, 'w', encoding='utf-8') as f:
        f.write(content)
    print("pyproject.toml updated successfully.")

    # 2. Create .github/workflows/wheels.yml
    wheels_yml_path = r'C:\Users\guest\Documents\GitHub\core-sg\.github\workflows\wheels.yml'
    os.makedirs(os.path.dirname(wheels_yml_path), exist_ok=True)
    wheels_yml_content = '''name: Build and Publish Wheels

on:
  push:
    tags:
      - "v*"          # Dispara em tags tipo v0.4.0, v1.0.0, etc.
  workflow_dispatch:  # Permite disparo manual pela aba Actions

jobs:
  build_wheels:
    name: Build wheels on ${{ matrix.os }}
    runs-on: ${{ matrix.os }}
    strategy:
      fail-fast: false
      matrix:
        os: [ubuntu-latest, windows-latest, macos-latest]

    steps:
      - uses: actions/checkout@v4

      - name: Set up Python
        uses: actions/setup-python@v5
        with:
          python-version: "3.11"

      - name: Install dependencies
        run: python -m pip install --upgrade pip build cibuildwheel

      - name: Build wheels
        run: python -m cibuildwheel --output-dir wheelhouse
        env:
          CIBW_ARCHS_MACOS: "x86_64 arm64"

      - name: Verify wheel contents
        run: |
          python -c "import glob, zipfile; [print(f) for f in glob.glob('wheelhouse/*.whl')]"
          python -c "
          import glob, zipfile
          for w in glob.glob('wheelhouse/*.whl'):
              with zipfile.ZipFile(w) as z:
                  names = z.namelist()
              assert any(n.endswith('.pyd') or n.endswith('.so') for n in names), f'Missing binary in {w}'
              print(f'OK: {w} contém binário compilado')
          "

      - name: Upload wheels as artifacts
        uses: actions/upload-artifact@v4
        with:
          name: wheels-${{ matrix.os }}
          path: wheelhouse/*.whl

  publish:
    name: Publish to TestPyPI
    needs: build_wheels
    if: startsWith(github.ref, 'refs/tags/')
    runs-on: ubuntu-latest

    steps:
      - uses: actions/download-artifact@v4
        with:
          path: dist
          merge-multiple: true

      - name: Publish to TestPyPI
        uses: pypa/gh-action-pypi-publish@v1.8.14
        with:
          repository-url: https://test.pypi.org/legacy/
          password: ${{ secrets.TEST_PYPI_TOKEN }}
'''
    with open(wheels_yml_path, 'w', encoding='utf-8') as f:
        f.write(wheels_yml_content)
    print("wheels.yml created successfully.")

    # 3. Update MANIFEST.in
    manifest_path = r'C:\Users\guest\Documents\GitHub\core-sg\MANIFEST.in'
    manifest_content = '''include README.md
include LICENSE
include THIRD_PARTY_NOTICES.md
recursive-include core_sg *.py *.pyx *.c *.h
prune build
global-exclude *.so
global-exclude *.pyd
global-exclude *.dll
recursive-include tests *.py
recursive-include benchmarks *.py
'''
    with open(manifest_path, 'w', encoding='utf-8') as f:
        f.write(manifest_content)
    print("MANIFEST.in updated successfully.")

if __name__ == "__main__":
    main()
