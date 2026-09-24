path = r'C:\Users\guest\Documents\GitHub\core-sg\pyproject.toml'
with open(path, 'r', encoding='utf-8') as f:
    text = f.read()
text = text.replace("3.1'2", "3.12")
with open(path, 'w', encoding='utf-8') as f:
    f.write(text)
print("Fixed typo in core-sg pyproject.toml")
