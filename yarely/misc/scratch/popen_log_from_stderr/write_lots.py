import sys
import time

count = 0
while True:
    count += 1
    sys.stdout.write('{count:=>100d}\n'.format(count=count))
    sys.stdout.flush()
    sys.stderr.write('{count:=>100d}\n'.format(count=count))
    sys.stderr.flush()
    time.sleep(5)