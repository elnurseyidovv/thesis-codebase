import os

root_dir = ''

for dirpath, filenames in os.walk(root_dir):
    if 'src/test/java' in dirpath:
        for filename in filenames:
            file_path = os.path.join(dirpath, filename)
            os.remove(file_path)
            print(f"deleted - {file_path}")