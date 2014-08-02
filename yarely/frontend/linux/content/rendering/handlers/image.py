import logging
import pexpect
from subprocess import Popen
from os import path, getenv, remove

image_bin = '/usr/bin/fim'

image_logfile = path.join(getenv('HOME'), 'image.log')

log = logging.getLogger(__name__)

class Image(object):
    def __init__(self, uri):
        # Set URL to render
        self.uri = uri

    def start(self):
        self.image = Popen([image_bin, self.uri])
        log.info('Fim started.')

    def wait(self):
        log.debug('Image waiting seen eof on process')
        self.image.terminate()
        log.debug('Image waiting cleanup')
        # Clean up after omxplayer
        if path.isfile(image_logfile):
            remove(image_logfile)
        log.debug('Image done')
