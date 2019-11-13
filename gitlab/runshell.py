import subprocess

proj = "repos-info-2-sheets"

is_the_truth = subprocess.call(["./git-clone.sh", proj])
