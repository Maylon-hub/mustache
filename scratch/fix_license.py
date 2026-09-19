from pathlib import Path

p = Path(r'C:\Users\guest\Documents\GitHub\core-sg\pyproject.toml')
content = p.read_text(encoding='utf-8')

# Fix license to string and remove license-files to satisfy setuptools
content = content.replace('license = { text = "BSD-3-Clause" }', 'license = "BSD-3-Clause"')
if 'license-files = [' in content:
    content = content.replace('license-files = ["LICENSE", "THIRD_PARTY_NOTICES.md"]\n', '')

p.write_text(content, encoding='utf-8')
print("Updated license in pyproject.toml")