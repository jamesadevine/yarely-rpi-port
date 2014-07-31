"""Render a movie on the Darwin platform via VLC"""

import logging

import AppKit
import Foundation
from PyObjCTools import AppHelper
import objc

from yarely.frontend.darwin.common.content.rendering import Renderer
from yarely.frontend.darwin.common.window import BaseWindow
from yarely.frontend.darwin.common.window.presentation import \
        FadingPresentationDelegate
from yarely.frontend.darwin.helpers.execution import application_loop
from yarely.frontend.darwin.content.rendering.handlers import libvlc

log = logging.getLogger(__name__)

APPLICATION_DESCRIPTION = "Render a movie on the Darwin platform via VLC"


class VLCRenderer(Renderer):
    def _handle_reply_params(self, msg_root, msg_elem):
        """A fudge until the Renderer Manager is in place."""
        super()._handle_reply_params(msg_root, msg_elem)

        self.uri = self.params['uri']

        log.info("URI is '{uri}'".format(uri=self.uri))
        AppHelper.callAfter(self.handle_prepare)

    def do_prepare(self):
        """Prepare an item of content for display."""

        window = VLCWindow.alloc().init()
        window.set_presentation_delegate(FadingPresentationDelegate())
        self.set_window(window)

        self.vlc_view = AppKit.NSView.alloc().initWithFrame_(
                Foundation.NSZeroRect)

        self.vlc_instance = libvlc.Instance(b"vlc", b"--no-video-title-show")
        self.vlc_media = self.vlc_instance.media_new(self.uri.encode())

        self.vlc_player = self.vlc_instance.media_player_new()
        self.vlc_player.set_media(self.vlc_media)
        self.vlc_player.set_nsobject(objc.pyobjc_id(self.vlc_view))
        self.vlc_player.video_set_deinterlace(b"linear")

        self.get_window().setContentView_(self.vlc_view)

        # Make the background black
        background_nscolour = AppKit.NSColor.\
                colorWithCalibratedRed_green_blue_alpha_(0, 0, 0, 1)
        self.get_window().setBackgroundColor_(background_nscolour)

    def do_became_visible(self):
        self.get_window().lock_level()
        self.vlc_player.play()


class VLCWindow(BaseWindow):
    def init(self):
        self.level_locked = False
        self = super().init()
        return self

    def setLevel_(self, windowLevel):
        if not self.level_locked:
            super().setLevel_(windowLevel)

    def lock_level(self):
        self.level_locked = True

if __name__ == "__main__":
    application_loop(VLCRenderer, description=APPLICATION_DESCRIPTION)
