# Start me with:
# $ PYTHONPATH="$HOME/proj" python3.2 -i renderer_harness.py

from yarely.frontend.core.helpers.base_classes import HandlerStub

from handler_harness import HandlerHarness, list_stubs, main, stubs


class RendererHarness(HandlerHarness):
    pass


python32_launch_str = "python3.2 -m {module}"

stubs.python32_darwin_image_renderer = HandlerStub(
        command_line_args=python32_launch_str.format(
            module="yarely.frontend.darwin.content.rendering.handlers.image"
            )
        )
stubs.python32_darwin_image_renderer.params_over_zmq = {
    "path": "/tmp/image.png"
}


stubs.python32_darwin_web_renderer = HandlerStub(
        command_line_args=python32_launch_str.format(
            module="yarely.frontend.darwin.content.rendering.handlers.web"
            )
        )
stubs.python32_darwin_web_renderer.params_over_zmq = {
    "uri": "http://pd-dev.lancs.ac.uk:8010/waterfall",
    #"layout_style": "fullscreen",
    "layout_style": "x_y_width_height",
    "layout_x": "50",
    "layout_y": "50",
    "layout_width": "100",
    "layout_height": "100",
}

stubs.python32_darwin_web_renderer_a = HandlerStub(
        command_line_args=python32_launch_str.format(
            module="yarely.frontend.darwin.content.rendering.handlers.web"
            )
        )
stubs.python32_darwin_web_renderer_a.params_over_zmq = {
    "uri": "http://www.lancs.ac.uk/",
    #"layout_style": "fullscreen",
    "layout_style": "x_y_width_height",
    "layout_x": "150",
    "layout_y": "150",
    "layout_width": "100",
    "layout_height": "100",
}

stubs.python32_darwin_movie_renderer = HandlerStub(
        command_line_args=python32_launch_str.format(
            module="yarely.frontend.darwin.content.rendering.handlers.qtmovie"
            )
        )
stubs.python32_darwin_movie_renderer.params_over_zmq = {
        "uri": "file:///tmp/movie.mov"
}

stubs.python32_darwin_vlc_renderer = HandlerStub(
        command_line_args=python32_launch_str.format(
            module="yarely.frontend.darwin.content.rendering.handlers.vlc"
            )
        )
stubs.python32_darwin_vlc_renderer.params_over_zmq = {
        "uri": "file:///tmp/movie.mov"
}

stubs.python32_darwin_rfb_renderer = HandlerStub(
        command_line_args=python32_launch_str.format(
            module="yarely.frontend.darwin.content.rendering.handlers.rfb"
            )
        )
stubs.python32_darwin_rfb_renderer.params_over_zmq = {
    "address": "192.168.125.254",
    "port": "5901",
    "password": "weed71risk",
    #"layout_style": "fullscreen",
    "layout_style": "x_y_width_height",
    "layout_x": "50",
    "layout_y": "50",
    "layout_width": "100",
    "layout_height": "100"
}


if __name__ == "__main__":
    harness = main(RendererHarness)
