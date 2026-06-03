import os

def search_files(directory, keyword):
    for root, dirs, files in os.walk(directory):
        for file in files:
            if file.endswith('.py') or file.endswith('.js') or file.endswith('.html'):
                path = os.path.join(root, file)
                try:
                    with open(path, 'r', encoding='utf-8') as f:
                        content = f.read()
                        if keyword in content:
                            print(f"Found '{keyword}' in {path}")
                            # print some lines around it
                            lines = content.split('\n')
                            for idx, line in enumerate(lines):
                                if keyword in line:
                                    start = max(0, idx - 2)
                                    end = min(len(lines), idx + 3)
                                    print(f"--- Line {idx+1} ---")
                                    for i in range(start, end):
                                        print(f"  {i+1}: {lines[i]}")
                except Exception as e:
                    pass

search_files('mustache', 'reachability_json')
search_files('mustache', 'reachability')
