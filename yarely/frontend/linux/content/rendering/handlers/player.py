import logging
import pexpect
from os import path, getenv, remove

player_bin = '/usr/bin/omxplayer'
omxplayer_logfile = path.join(getenv('HOME'), 'omxplayer.log')
omxplayer_old_logfile = path.join(getenv('HOME'), 'omxplayer.old.log')

log = logging.getLogger(__name__)

class Player(object):
    def __init__(self, uri):
        self.player = pexpect.spawn('%s %s' % (player_bin, uri))
        self.uri=uri

    def start(self):
        # do not use '-s' flag (not needed, will give lots of unneeded output)
        self.player.send('p')

    def wait(self):
        self.player.expect(pexpect.EOF, timeout=None)
        self.player.terminate(force=True)
        # Clean up after omxplayer
        if path.isfile(omxplayer_old_logfile):
            remove(omxplayer_old_logfile)
        elif path.isfile(omxplayer_logfile):
            remove(omxplayer_logfile)
        print('Player DONE')
