import logging
import socket
import struct
import threading

import pyDes

log = logging.getLogger(__name__)


class RFB:
    def __init__(self, delegate):
        self.delegate = delegate
        self.in_use = False

    def connect(self, address, port, password):
        assert self.in_use is False, "Already in use"
        self.in_use = True

        self.framebuffer_update_request_event = threading.Event()

        self.address = address
        self.port = port
        self.password = password

        self.start_socket_worker()

    def start_socket_worker(self):
        self.socket_worker_thread = threading.Thread(target=self.socket_worker)
        self.socket_worker_thread.name = "RFB Socket Worker"
        self.socket_worker_thread.daemon = True
        self.socket_worker_thread.start()

    def request_updated_framebuffer(self):
        self.framebuffer_update_request_event.set()

    def socket_worker(self):
        server = socket.socket()

        self.call_delegate_method("connecting")

        try:
            server.connect((self.address, self.port))
        except Exception as e:
            self.call_delegate_method("connection_failed", e)
            self.in_use = False
            return

        self.call_delegate_method("connected")

        response = self.read_from_socket(server, 12)

        if not response.startswith(b'RFB '):
            self.call_delegate_method("connection_failed",
                    "handshake incorrect")
            self.in_use = False

            return

        major = response[4:7]
        minor = response[8:11]

        log.info("Server reports RFB " + major.decode() + "." + minor.decode())

        if major != b"003":
            self.call_delegate_method("connection_failed",
                "Unexpected server major version ({major!r}, expected 3)".\
                        format(major=major))
            self.in_use = False

            return

        server.sendall(b"RFB 003.003\n")

        response = self.read_from_socket(server, 4)

        if response != b"\x00\x00\x00\x02":
            self.call_delegate_method("connection_failed",
                "Unexpected security type ({response!r}) - expected '2'".\
                        format(response=response))
            self.in_use = False
            return

        log.debug("Using VNC authentication")

        response = self.read_from_socket(server, 16)

        # Turn the password string into bytes, pad with NULL and cut to
        # 8 bytes.
        pw_bytes = self.password.encode()
        pw_bytes = pw_bytes.ljust(8, b'\x00')
        pw_bytes = pw_bytes[:8]

        des = RFBDes(pw_bytes)
        des_data = des.encrypt(response)

        server.sendall(des_data)

        response = self.read_from_socket(server, 4)
        if response != b'\x00\x00\x00\x00':
            self.call_delegate_method("connection_failed",
                "Unexpected security response ({response!r}) - expected '0'".\
                        format(response=response))
            self.in_use = False
            return

        log.debug("Authenticated")

        # share the desktop
        server.sendall(b"\x01")

        width_response = self.read_from_socket(server, 2)
        height_response = self.read_from_socket(server, 2)
        pixel_format_response = self.read_from_socket(server, 16)
        name_length_response = self.read_from_socket(server, 4)

        self.desktop_width = struct.unpack(">H", width_response)[0]
        self.desktop_height = struct.unpack(">H", height_response)[0]

        (bits_per_pixel, depth, big_endian, true_colour, red_max, green_max,
            blue_max, red_shift, green_shift, blue_shift) = struct.unpack(
                ">BBBBHHHBBBxxx", pixel_format_response)

        bytes_per_pixel = bits_per_pixel // 8

        name_length = struct.unpack(">I", name_length_response)[0]

        name = self.read_from_socket(server, name_length)

        log.info("Desktop: {width}x{height}".format(
            width=self.desktop_width, height=self.desktop_height))

        log.debug("bits per pixel: {}".format(bits_per_pixel))
        log.debug("depth: {}".format(depth))
        log.debug("big_endian: {}".format(big_endian))
        log.debug("true_colour: {}".format(true_colour))
        log.debug("rgb max: {}/{}/{}".format(red_max, green_max, blue_max))
        log.debug("rgb shift: {}/{}/{}".format(red_shift, green_shift,
            blue_shift))

        log.info("Name: {}".format(name))

        self.call_delegate_method("generate_memory_view", self.desktop_width,
                self.desktop_height)

        first_update = True

        while True:
            self.framebuffer_update_request_event.wait()
            self.framebuffer_update_request_event.clear()

            message_type = 3
            x_pos = 0
            y_pos = 0
            width = self.desktop_width
            height = self.desktop_height

            if first_update:
                incremental = 0
                first_update = False
            else:
                incremental = 1

            log.info("Sending framebuffer update request")

            framebuffer_update_request = struct.pack(">BBHHHH",
                    message_type, incremental, x_pos, y_pos, width, height)
            server.sendall(framebuffer_update_request)

            response = self.read_from_socket(server, 4)

            (message, num_rects) = struct.unpack(">BxH", response)

            if message != 0:
                self.call_delegate_method("connection_closed",
                    ("Unexpected framebuffer update response ({response!r}) "
                     "- expected '0'").format(response=response))
                self.in_use = False
                return

            log.info("Saw framebuffer update with {} rects".format(num_rects))

            for rect_num in range(num_rects):
                #log.info("Handling rect {}".format(rect_num))

                response = self.read_from_socket(server, 12)

                (x_pos, y_pos, width, height, enc_type) = struct.unpack(
                        ">HHHHL", response)

                #log.info("XY {}x{}, WH {}x{}".format(x_pos, y_pos, width,
                #    height))

                if enc_type != 0:
                    self.call_delegate_method("connection_closed",
                        ("Unexpected framebuffer encoding ({response!r}) - "
                         "expected '0'").format(response=response))
                    self.in_use = False
                    return

                rect_data = self.read_from_socket(server, bytes_per_pixel *
                        height * width)

                log.warn(len(rect_data))

                for row in range(height):
                    for col in range(width):
                        rect_data_offset = row * width * bytes_per_pixel
                        rect_data_offset += col * bytes_per_pixel
                        rfb_pixel_start = rect_data_offset
                        rfb_pixel_end = rect_data_offset + bytes_per_pixel

                        rfb_pixel = rect_data[rfb_pixel_start:rfb_pixel_end]

                        if bytes_per_pixel == 1:
                            pixel_format = "B"
                        elif bytes_per_pixel == 2:
                            pixel_format = "H"
                        else:
                            pixel_format = "L"

                        pixel = struct.unpack(pixel_format, rfb_pixel)[0]

                        red = (pixel >> red_shift) & red_max
                        green = (pixel >> green_shift) & green_max
                        blue = (pixel >> blue_shift) & blue_max

                        pixel_idx = (y_pos + row) * self.desktop_width * 3
                        pixel_idx += (x_pos + col) * 3
                        red_idx = pixel_idx
                        end_idx = pixel_idx + 3

                        self.framebuffer_mv[red_idx:end_idx] = bytes(
                                (int((red / red_max) * 255),
                                 int((green / green_max) * 255),
                                 int((blue / blue_max) * 255)))

            self.call_delegate_method("updated_pixmap")

    def read_from_socket(self, sock, n_bytes):
        recv_buffer = b''
        while len(recv_buffer) < n_bytes:
            recv_buffer += sock.recv(n_bytes - len(recv_buffer))

        return recv_buffer

    def call_delegate_method(self, name, *args, **kwargs):
        method = getattr(self.delegate, name, None)
        if method is None:
            return
        method(self, *args, **kwargs)


# Shamefully stolen from
# http://code.google.com/p/python-vnc-viewer/source/browse/rfb.py
class RFBDes(pyDes.des):
    def setKey(self, key):
        """RFB protocol for authentication requires client to encrypt
           challenge sent by server with password using DES method. However,
           bits in each byte of the password are put in reverse order before
           using it as encryption key."""
        newkey = bytearray()
        for ki in range(len(key)):
            bsrc = key[ki]
            btgt = 0
            for i in range(8):
                if bsrc & (1 << i):
                    btgt = btgt | (1 << 7 - i)
            newkey.append(btgt)
        super(RFBDes, self).setKey(bytes(newkey))
