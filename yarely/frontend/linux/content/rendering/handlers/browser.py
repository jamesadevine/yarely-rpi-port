import logging
from subprocess import Popen
from os import path, getenv, remove

netsurf_bin = '/usr/bin/netsurf-fb'

browser_logfile = path.join(getenv('HOME'), 'netsurf.log')

log = logging.getLogger(__name__)

class Browser(object):
    def __init__(self, uri,resolution):
        # Set URL to render
        self.uri = uri
        width_height=resolution.strip('+0+0')
        split_width_height=width_height.split('x')
        self.width=split_width_height[0]
        self.height=split_width_height[1]

    def start(self):
        #need -b 16 for rasp pi as netsurf cannot automatically detect color depth
        self.browser = Popen([netsurf_bin,'-w',self.width,'-h',self.height, '-b', '16',self.uri])
        #self.browser = pexpect.spawn('%s -b 16 %s' % (netsurf_bin, self.uri))
        print(str(self.browser))
        log.info(self.browser)
        log.info('netsurf started.')

    def wait(self):
        log.debug('netsurf waiting for eof on process')
        log.debug('netsurf waiting seen eof on process')
        self.browser.kill()
        log.debug('netsurf waiting cleanup')
        # Clean up after omxplayer
        if path.isfile(browser_logfile):
            remove(browser_logfile)
        log.debug('netsurf done')
