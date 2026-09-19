import mustache
import os

print("mustache path:", mustache.__file__)
print("mustache package directory contents:")
try:
    pkg_dir = os.path.dirname(mustache.__file__)
    print("pkg_dir:", pkg_dir)
    print("Files in pkg_dir:")
    print(os.listdir(pkg_dir))
    
    # Check core
    core_dir = os.path.join(pkg_dir, 'core')
    print("Files in core_dir:")
    print(os.listdir(core_dir))
except Exception as e:
    print("Error:", e)
