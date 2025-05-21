import os, sys
import subprocess
import logging as log

def is_valid_data_line(line: str) -> bool:
    return (
        line.count('\t') == 1
        and line.startswith('/')
        and all(c.isdigit() or c == '.' for c in line.split('\t')[1])
    )

log.basicConfig(level=log.ERROR)

rootdir = sys.argv[1]
verbose = "--verbose" in sys.argv
chunk_size = 500
rsm_jar = "rsm.jar"
java_files = []

for subdir, _, files in os.walk(rootdir):
    for f in files:
        java_files.append(os.path.join(subdir, f))

def run_chunk(chunk):
    cmd = ["java", "-jar", rsm_jar] + chunk
    p = subprocess.Popen(cmd, stdout=subprocess.PIPE, stderr=subprocess.STDOUT)
    out, _ = p.communicate()
    lines = out.decode("utf-8", errors="ignore").splitlines()
    if p.returncode != 0 and verbose:
        log.error(f"exited - {p.returncode}")
    return lines

all_lines = []
for i in range(0, len(java_files), chunk_size):
    print("new 500 files")
    chunk = java_files[i : i + chunk_size]
    all_lines.extend(run_chunk(chunk))

entries = []
for line in all_lines:
    if not is_valid_data_line(line):
        if verbose and line.strip() and not line.startswith("file\t"):
            log.error(f"invalid line: {line}")
        continue
    path, score = line.split('\t')
    entries.append((path, score))

with open("report.csv", "w") as out:
    out.write("file_name,score,level\n")
    for path, score in entries:
        out.write(f"{path},{score}\n")
