import subprocess

proj = "ah"

if(subprocess.call(["./git-clone.sh", proj])):
    print("Yes")

