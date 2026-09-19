filePath = r"C:\Users\guest\Documents\GitHub\core-sg\core_sg\core_sg.py"
with open(filePath, 'r', encoding='utf-8') as f:
    content = f.read()

# Remove sort_core_sg from build_core_sg_from_data
content = content.replace("    core_sg = sort_core_sg(core_sg)\n", "    # core_sg remains unsorted so knng_to_insert and mst_tmp remain structured for slicing\n")

with open(filePath, 'w', encoding='utf-8') as f:
    f.write(content)

print("Removed sort_core_sg from build_core_sg_from_data!")