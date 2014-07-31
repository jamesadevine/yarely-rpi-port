"""Render a RFB connection on the Darwin platform."""

import logging

import AppKit
import Foundation
from PyObjCTools import AppHelper

# FIXME - this should be a standalone library really
from yarely.frontend.core.helpers.rfb import RFB

from yarely.frontend.darwin.common.content.rendering import \
        Renderer, PREPARATION_NOT_YET_COMPLETE
from yarely.frontend.darwin.common.view.image_view import CenteredImageView
from yarely.frontend.darwin.common.window.layout import \
        XYWidthHeightLayoutDelegate
from yarely.frontend.darwin.helpers.execution import application_loop

log = logging.getLogger(__name__)

APPLICATION_DESCRIPTION = "Render an RFB display on the Darwin platform"


class RFBDelegate:
    def __init__(self, rfb_renderer, fb_image):
        self.rfb_renderer = rfb_renderer
        self.fb_image = fb_image

        self.first_pixmap_update = True

        self.bitmap_image_rep = None

    def connecting(self, sender):
        log.info("connecting")

    def connection_failed(self, sender, cause):
        log.warn("Connection failed, {cause!r}".format(cause=cause))
        self.rfb_renderer.prepare_failed()

    def generate_memory_view(self, sender, width, height):
        AppHelper.callAfter(self._generate_memory_view, sender, width, height)

    def _generate_memory_view(self, sender, width, height):
        log.info("connected")
        self.bitmap_image_rep = AppKit.NSBitmapImageRep.alloc().initWithBitmapDataPlanes_pixelsWide_pixelsHigh_bitsPerSample_samplesPerPixel_hasAlpha_isPlanar_colorSpaceName_bytesPerRow_bitsPerPixel_(None, sender.desktop_width, sender.desktop_height, 8, 3, False, False, AppKit.NSCalibratedRGBColorSpace, sender.desktop_width * 3, 0)
        sender.framebuffer_mv = self.bitmap_image_rep.bitmapData()

        sender.request_updated_framebuffer()

    def updated_pixmap(self, sender):
        AppHelper.callAfter(self._updated_pixmap, sender)

    def _updated_pixmap(self, sender):
        if self.first_pixmap_update:
            self.first_pixmap_update = False
            self.rfb_renderer.set_new_image_rep(self.bitmap_image_rep)
        else:
            self.rfb_renderer.refresh_image()

        sender.framebuffer_mv = self.bitmap_image_rep.bitmapData()

        AppHelper.callLater(0.1, sender.request_updated_framebuffer)


class RFBRenderer(Renderer):
    def _handle_reply_params(self, msg_root, msg_elem):
        """A fudge until the Renderer Manager is in place."""
        super()._handle_reply_params(msg_root, msg_elem)
        self.rfb_address = self.params['address']
        self.rfb_port = int(self.params['port'])
        self.rfb_password = self.params['password']

        msg = "rfb://{address}:{port}"
        log.info(msg.format(address=self.rfb_address, port=self.rfb_port))
        AppHelper.callAfter(self.handle_prepare)

    def do_prepare(self):
        """Prepare an item of content for display."""

        self.current_image_rep = None
        self.view = None

        self.fb_image = AppKit.NSImage.alloc().\
                initWithSize_(Foundation.NSZeroSize)

        self.rfb_delegate = RFBDelegate(self, self.fb_image)

        self.rfb = RFB(self.rfb_delegate)

        self.rfb.connect(self.rfb_address, self.rfb_port, self.rfb_password)

        return PREPARATION_NOT_YET_COMPLETE

    def set_new_image_rep(self, image_rep):
        self.fb_image.addRepresentation_(image_rep)

        if self.current_image_rep is not None:
            self.fb_image.removeRepresentation_(self.current_image_rep)

        self.current_image_rep = image_rep

        if self.view is None:
            self.rfb_complete_preparation()

    def refresh_image(self):
        self.view.setNeedsDisplay_(True)

    def rfb_complete_preparation(self):
        # This doesn't really belong here...
        if self.params["layout_style"] == "x_y_width_height":
            layout_delegate = XYWidthHeightLayoutDelegate(
                    int(self.params["layout_x"]),
                    int(self.params["layout_y"]),
                    int(self.params["layout_width"]),
                    int(self.params["layout_height"]))
            self.get_window().set_layout_delegate(layout_delegate)

        self.view = CenteredImageView.alloc().initWithImage_scale_(
            self.fb_image, 1)
        self.get_window().setContentView_(self.view)

        # Make the background black
        background_nscolour = AppKit.NSColor.\
                colorWithCalibratedRed_green_blue_alpha_(0, 0, 0, 1)
        self.get_window().setBackgroundColor_(background_nscolour)

        self.prepare_successful()

if __name__ == "__main__":
    application_loop(RFBRenderer, description=APPLICATION_DESCRIPTION)
