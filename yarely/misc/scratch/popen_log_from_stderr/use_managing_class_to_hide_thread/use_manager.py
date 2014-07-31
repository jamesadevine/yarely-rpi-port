import logging
import os.path
import time
from subprocess import Popen, PIPE
from threading import Thread

path = '/Users/sarah/Documents/LancasterUniversity/PhD/yarely/scratch/popen_log_from_stderr'


class Test_UseSubclassOfThread:
    def __init__(self):
        self.processes = {}
        self.log = logging.getLogger('yarely.scratch')
        self.log.setLevel(logging.DEBUG)
        handler = logging.FileHandler(filename='/tmp/yarely_test.log')
        handler.setLevel(logging.DEBUG)
        self.log.addHandler(handler)
        
    def _run_popen(self, uri):
        subproc = SubprocessWithErrorCapturing(uri)
        self.processes[uri] = subproc

    def _stop_popen(self, uri):
        if uri in self.processes:
            self.processes[uri]._stop_popen()

    def test(self):
        self._run_popen('foo')
        time.sleep(10)
        self._stop_popen('foo')


class SubprocessWithErrorCapturing:
    def __init__(self, uri):
        self.uri = uri
        self.log = logging.getLogger('yarely.scratch')
        self._run_popen()

    def _run_popen(self):
        args = ['python3.2', os.path.join(path, 'write_lots.py')]
        with Popen(args, stderr=PIPE) as self.subproc:
            self.error_reader = Thread(target=self._error_reader)
            self.error_reader.start()

    def _stop_popen(self):
        if None not in (self.subproc, self.subproc.poll()):
            try:
                self.subproc.terminate()
            except:
                pass
            time.sleep(0.1)
            retcode = self.subproc.poll()
            if retcode is None:          
                self.log.warning('Subprocess did not terminate, sending kill')               
                try:
                    self.subproc.kill()
                except:
                    pass
                time.sleep(0.1)
                retcode = self.subproc.poll()
                if retcode is None:
                    self.log.warning('Subprocess did not respond to kill')
        if self.error_reader.is_alive():
            self.error_reader.join() # maybe a bad idea?

    def _error_reader(self):
        while self.subproc.poll() is None:
            try:
                self.log.debug(self.subproc.stderr.readline())
            except:
                pass


if __name__ == '__main__':
    t = Test_UseSubclassOfThread()
    t.test()
    time.sleep(10)
