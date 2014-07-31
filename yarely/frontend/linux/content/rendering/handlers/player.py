import logging
import pexpect
from os import path, getenv, remove

player_bin = '/usr/bin/omxplayer'
omxplayer_logfile = path.join(getenv('HOME'), 'omxplayer.log')
omxplayer_old_logfile = path.join(getenv('HOME'), 'omxplayer.old.log')

log = logging.getLogger(__name__)

class Player(object):
    def __init__(self, uri):
        # do not use '-s' flag (not needed, will give lots of unneeded output)
        self.player = pexpect.spawn('%s %s' % (player_bin, uri))
        log.info('Player started.')


        log.debug('Player init done')

    def start(self):
        self.player.send('p')
        log.debug('Player init written command')

        # wait for  Subtitle count
        while True:
            #log.debug('Player init in loop')
            l = self.player.readline()
            if not l:
                log.debug('Player init read eof')
                break
            log.debug('Player init read line: "%s"' % l)
            if "Subtitle count" in l:
                break
        log.debug('Player start written command')

    def wait(self):
        log.debug('Player waiting for eof on process')
        self.player.expect(pexpect.EOF, timeout=None)
        log.debug('Player waiting seen eof on process')
        self.player.terminate(force=True)
        log.debug('Player waiting cleanup')
        # Clean up after omxplayer
        if path.isfile(omxplayer_old_logfile):
            remove(omxplayer_old_logfile)
        elif path.isfile(omxplayer_logfile):
            remove(omxplayer_logfile)
        log.debug('Player done')
