import os

def find_files(directory, name):
    for root, dirs, files in os.walk(directory):
        for file in files:
            if file == name:
                print(os.path.join(root, file))

find_files('.', 'clustering.py')
find_files('.', 'batch.py')
