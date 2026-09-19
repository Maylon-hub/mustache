from pathlib import Path

p = Path(r'C:\Users\guest\Documents\GitHub\core-sg\pyproject.toml')
text = p.read_text(encoding='utf-8-sig')  # strip BOM if present
p.write_text(text, encoding='utf-8')       # write UTF-8 without BOM
print('Fixed BOM in pyproject.toml')