filePath = r"C:\Users\guest\Documents\GitHub\core-sg\core_sg\core_sg.py"
with open(filePath, 'r', encoding='utf-8') as f:
    content = f.read()

# Fix __future__ import position
content = content.replace("import hdbscan\nfrom __future__ import annotations\n", "from __future__ import annotations\nimport hdbscan\n")

with open(filePath, 'w', encoding='utf-8') as f:
    f.write(content)
print("Fixed __future__ import order in core_sg.py")