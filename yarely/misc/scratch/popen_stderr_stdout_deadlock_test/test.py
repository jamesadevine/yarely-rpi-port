import os.path
from subprocess import Popen, PIPE

path = '/Users/sarah/Documents/LancasterUniversity/PhD/yarely/frontend/core/subscriptions/popen_stderr_stdout_test'

#with Popen(["python3.2", os.path.join(path, 'write_lots.py')], stdout=PIPE, stderr=PIPE) as proc:
with Popen(["python3.2", os.path.join(path, 'write_lots.py')], stderr=PIPE) as proc:
    s = proc.stderr.read(100)
    while s:
     print(">{0}".format(s))
     s = proc.stderr.read(100)