import logging
import os.path
import time
from subprocess import Popen, PIPE
from threading import Thread

path = '/Users/sarah/Documents/LancasterUniversity/PhD/yarely/scratch/popen_log_from_stderr'


class Test_UseThreadDirectly:
    def __init__(self):
        self.processes = {}
        self.error_readers = {}
        self.log = logging.getLogger('yarely.scratch')
        self.log.setLevel(logging.DEBUG)
        handler = logging.FileHandler(filename='/tmp/yarely_test.log')
        handler.setLevel(logging.DEBUG)
        self.log.addHandler(handler)

    def _run_popen(self, uri):
        if uri not in self.processes:
            args = ['python3.2', os.path.join(path, 'write_lots.py')]
            with Popen(args, stderr=PIPE) as subproc:
                self.processes[uri] = subproc
                error_reader = Thread(target=self._error_reader, args=(subproc,))
                error_reader.start()
                self.error_readers[uri] = error_reader

    def _stop_popen(self, uri):
        if uri in self.processes:
            if None not in (self.processes[uri], self.processes[uri].poll()):
                try:
                    self.processes[uri].terminate()
                except:
                    pass
                time.sleep(0.1)
                retcode = self.processes[uri].poll()
                if retcode is None:          
                    self.log.warning('Subprocess did not terminate, sending kill')               
                    try:
                        self.processes[uri].kill()
                    except:
                        pass
                    time.sleep(0.1)
                    retcode = self.processes[uri].poll()
                    if retcode is None:
                        self.log.warning('Subprocess did not respond to kill')
            self.processes.pop(uri)
        if uri in self.error_readers:
            if self.error_readers[uri].is_alive():
                self.error_readers[uri].join()  # maybe a bad idea?
            self.error_readers.pop(uri)

    def test(self):
        self._run_popen('foo')
        time.sleep(10)
        self._stop_popen('foo')


    def _error_reader(self, subproc):
        while subproc.poll() is None:
            try:
                self.log.debug(subproc.stderr.readline())
            except:
                pass
                
if __name__ == '__main__':
    t = Test_UseThreadDirectly()
    t.test()
    time.sleep(10)