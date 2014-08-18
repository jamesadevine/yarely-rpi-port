import logging
import subprocess
from os import path, getenv

shutter_bin = path.join(getenv('HOME'), 'proj', 'yarely',
                        'frontend', 'linux', 'shutter',
                        'shutter.bin')

log = logging.getLogger(__name__)

class Shutter(object):
    # FIXME we only look at stdout of fade program;
    # instead, we should also watch its stderr.
    # moreover, what if something goes wrong and we hang forever in readline() ?
    # should we use a timer to be robust against that?
    def __init__(self):
        self.shutter = None
        shutter_args = [shutter_bin]
        self.shutter = subprocess.Popen(
            shutter_args, bufsize=-1,
            stdin=subprocess.PIPE, stdout=subprocess.PIPE
        )

    # color must either be 'black' or 'white'
    # or something like '0xFF0000' (for red), '0x0000FF' (for blue),
    # or '0x292929' (very dark non-black),  '0xCCCCCC' (grey)
    def fade_to(self, color):
        if color == 'white':
            self.fade_to_white()
        elif color == 'black':
            self.fade_to_black()
        else:
            self.fade_to_color(color)

    def fade_to_black(self):
        #print('fade out')
        self.issue_command('fade-to-black\n', 'fade_to_black')

    def fade_to_white(self):
        self.issue_command('fade-to-white\n', 'fade_to_white')

    def fade_to_color(self, color):
        self.issue_command('fade-to-color %s\n' % color, 'fade_to_color')

    def fade_in(self):
        #print('fade in')
        self.issue_command('fade-in\n', 'fade_in')

    def hard_to(self, color):
        if color == 'white':
            self.hard_to_white()
        elif color == 'black':
            self.hard_to_black()
        else:
            self.hard_to_color(color)

    def hard_to_black(self):
        self.issue_command('hard-to-black\n', 'hard_to_black')

    def hard_to_white(self):
        self.issue_command('hard-to-white\n', 'hard_to_white')

    def hard_to_color(self, color):
        self.issue_command('hard-to-color %s\n' % color, 'hard_to_color')

    def hard_in(self):
        self.issue_command('hard-in\n', 'hard_in')

    def issue_command(self, command, function_name):
        if not self.shutter:
                return
        logging.debug('%s start' % function_name)
        try:
            self.shutter.stdin.write(bytes(command, 'ascii'))
            self.shutter.stdin.flush()
            l = self.shutter.stdout.readline().decode('UTF-8')
        except IOError:
            shutter_args = [shutter_bin]
            self.shutter=None
            self.shutter = subprocess.Popen(
                shutter_args, bufsize=-1,
                stdin=subprocess.PIPE, stdout=subprocess.PIPE
            )
            logging.debug('IO ERROR: Restarting the shutter...')
            return
        # logging.debug('%s read "%s"' % (function_name, l))
        logging.debug('%s read end' % function_name)
