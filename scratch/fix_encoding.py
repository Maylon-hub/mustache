filePath = r"C:\Users\guest\Documents\GitHub\mustache\scripts\benchmark_coresg_vs_hdbscan_canonical.py"
with open(filePath, "r", encoding="utf-8") as f:
    content = f.read()

# Add sys.stdout.reconfigure(encoding='utf-8') at start of main()
old_main = "def main():"
new_main = "def main():\n    if hasattr(sys.stdout, 'reconfigure'):\n        sys.stdout.reconfigure(encoding='utf-8')"

content = content.replace(old_main, new_main)

# Replace emoji 🏆 with [WIN] in terminal print statements
content = content.replace("🏆 CoreSG", "CoreSG")
content = content.replace("🏆 (Core-SG", "(Core-SG")

with open(filePath, "w", encoding="utf-8") as f:
    f.write(content)

print("Fixed UTF-8 stdout encoding in benchmark_coresg_vs_hdbscan_canonical.py!")