filePath = r"C:\Users\guest\Documents\GitHub\core-sg\core_sg\core_sg.py"
with open(filePath, 'r', encoding='utf-8') as f:
    content = f.read()

if "import hdbscan" not in content:
    content = "import hdbscan\n" + content
    with open(filePath, 'w', encoding='utf-8') as f:
        f.write(content)
    print("Added import hdbscan to core_sg.py")
else:
    print("import hdbscan already present")