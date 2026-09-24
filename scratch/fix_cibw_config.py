import os

path = r'C:\Users\guest\Documents\GitHub\core-sg\pyproject.toml'
with open(path, 'r', encoding='utf-8') as f:
    content = f.read()

# Replace build line
content = content.replace('build = "cp310-* cp311-* cp312-* cp313-* cp314-*"', 'build = "cp310-* cp311-* cp312-* cp313-*"')

# Add test-requires if not present
if 'test-requires' not in content:
    content = content.replace(
        'skip = ["*-musllinux_*", "*-manylinux_i686", "pp*"]',
        'skip = ["*-musllinux_*", "*-manylinux_i686", "pp*"]\ntest-requires = ["scikit-learn>=1.3", "numpy>=1.24,<3", "pandas>=2.0"]'
    )

# Add test-skip under macos section if not present
if 'test-skip = "*_x86_64"' not in content:
    content = content.replace(
        '[tool.cibuildwheel.macos]\narchs = ["x86_64", "arm64"]',
        '[tool.cibuildwheel.macos]\narchs = ["x86_64", "arm64"]\ntest-skip = "*_x86_64"'
    )

# Remove duplicate test-command line under linux section if present
content = content.replace('\n[tool.cibuildwheel.linux]\nmanylinux-x86_64-image = "manylinux2014"\ntest-command = "python -c \\"from sklearn.datasets import make_blobs; from core_sg import CoreSG; X, _ = make_blobs(n_samples=120, n_features=3, centers=3, random_state=42); core = CoreSG(metric=\'euclidean\', p=2); core.fit(X, k_max=5); mst = core.extract_mst_from_core_sg(k=3); assert mst is not None\\""', '\n[tool.cibuildwheel.linux]\nmanylinux-x86_64-image = "manylinux2014"')

with open(path, 'w', encoding='utf-8') as f:
    f.write(content)

print("Updated core-sg pyproject.toml cibuildwheel configuration successfully.")
