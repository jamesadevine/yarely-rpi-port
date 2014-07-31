#!/usr/bin/env python3.2

# I will output the main screen's width and height in a format that
# BASH can 'eval'.  Use me like so:
# eval `./darwin_screen_resolution.py`
# echo $SCREEN_WIDTH x $SCREEN_HEIGHT

import AppKit

OUTPUT_TEMPLATE = "SCREEN_WIDTH={width:.0f} SCREEN_HEIGHT={height:.0f}"

screen_size = AppKit.NSScreen.mainScreen().frame().size

output = OUTPUT_TEMPLATE.format(width=screen_size.width,
        height=screen_size.height)

print(output)
