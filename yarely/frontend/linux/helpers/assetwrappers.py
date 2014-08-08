import logging
from time import sleep

log = logging.getLogger(__name__)

from yarely.frontend.linux.content.rendering.handlers.image import Image
from yarely.frontend.linux.content.rendering.handlers.player import Player
from yarely.frontend.linux.content.rendering.handlers.browser import Browser
import yarely.frontend.linux.content.rendering.html_templates as html_templates

class BaseAsset(object):
    def __init__(self, asset, renderers):
        self.asset = asset
        self.renderers = renderers

    def prepare(self):
        raise NotImplementedError

    def play(self):
        raise NotImplementedError

    def stop(self):
        raise NotImplementedError

    def name(self):
        return self.asset["name"]

    def fade_colour(self):
        raise NotImplementedError
        
    def should_precache(self):
        raise NotImplementedError
    
    def set_uri(self, uri):
        self.uri = uri
        
class ImageAsset(BaseAsset):
    def __init__(self, *args, **kwargs):
        super(ImageAsset, self).__init__(*args, **kwargs)
        self.player = None

    def prepare(self):
        self.image = Image(self.uri)

    def play(self):
        # now that we just show a black background,
        # it makes no sense to waste time by fading in
        # shutter.fade_in()
        #self.renderers.shutter.fade_in()

        if self.image:
            self.image.start()

    def stop(self):
        #self.renderers.shutter.fade_to_black()
        if self.image:
            self.image.wait()

    def fade_colour(self):
        return 'black'

    def should_precache(self):
        return True

class BrowserAsset(BaseAsset):
    def __init__(self, *args, **kwargs):
        super(BrowserAsset, self).__init__(*args, **kwargs)
        self.browser = None

    def prepare(self):
        self.browser = Browser(self.uri)

    def play(self):
        # now that we just show a black background,
        # it makes no sense to waste time by fading in
        # shutter.fade_in()
        #self.renderers.shutter.fade_in()

        if self.browser:
            self.browser.start()

    def stop(self):
        #self.renderers.shutter.fade_to_black()
        if self.browser:
            self.browser.wait()

    def fade_colour(self):
        return 'black'

    def should_precache(self):
        return True

'''
alternative browser class for loading live links - not recommended it's very bad (no javascript)
class BrowserAsset(BaseAsset):
    def __init__(self, *args, **kwargs):
        super(BrowserAsset, self).__init__(*args, **kwargs)
        self.browser = None

    def prepare(self):
        self.browser = Browser(self.uri,self.renderers.resolution)

    def play(self):
        # now that we just show a black background,
        # it makes no sense to waste time by fading in
        # shutter.fade_in()
        self.renderers.shutter.hard_in()

        if self.browser:
            self.browser.start()

    def stop(self):
        if self.browser:
            self.browser.wait()
        self.renderers.shutter.fade_to_black()

    def fade_colour(self):
        return 'black'

    def should_precache(self):
        return False
'''

class PlayerAsset(BaseAsset):
    def __init__(self, *args, **kwargs):
        super(PlayerAsset, self).__init__(*args, **kwargs)
        self.player = None

    def prepare(self):
        self.player = Player(self.uri)

        # now that we just show a black background,
        # it makes no sense to waste time by fading in
        #self.shutter.fade_in()
        if self.player:
            self.player.start()

    def stop(self):
        if self.player:
            self.player.wait()

    def fade_colour(self):
        return 'black'

    def should_precache(self):
        return True
