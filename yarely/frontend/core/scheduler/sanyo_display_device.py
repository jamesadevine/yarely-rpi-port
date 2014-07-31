import sys
import termios
import time

LINESPEED_DISPLAY = termios.B19200
INTER_COMMAND_SPACING = 0.2  # 0.6 is max value
timestamps_last_command = {}
USB_SERIAL = '/dev/tty.usbserial-'


class Display():
    def buf_to_string(self, buf):
        s = ''
        for i in buf:
            if type(i) is str:
                s = s + ' 0x%x' % ord(i)
            else:
                s = s + ' 0x%x' % i
        return s

    def open_device(self, display_serial, linespeed):
        fd_display = open(display_serial, 'w+')
        # Set baud and line control bits
        attrs = termios.tcgetattr(fd_display)
        attrs[0] = attrs[0] & ~termios.IXON
        attrs[0] = attrs[0] & ~termios.IXOFF
        attrs[3] = attrs[3] & ~termios.ECHO
        attrs[4] = LINESPEED_DISPLAY
        attrs[5] = LINESPEED_DISPLAY
        print("main: setting line attributes: projector")
        termios.tcsetattr(fd_display, termios.TCSANOW, attrs)
        termios.tcsetattr(fd_display, termios.TCSANOW, attrs)
        return fd_display

    def send_sequence_to_projector(
        self, fd_out, buf, respect_inter_command_spacing=True
    ):
        print("IN, command is >>>{cmd}<<<, to be sent to fd {fd}".format(
            cmd=self.buf_to_string(buf), fd=repr(fd_out)
        ))
        global timestamps_last_command, INTER_COMMAND_SPACING
        if fd_out not in timestamps_last_command:
            timestamps_last_command[fd_out] = 0
        if(respect_inter_command_spacing):
            current_time = time.time()
            print("checking inter-command spacing: %f vs. %f" % (
                timestamps_last_command[fd_out], current_time))
            delta = current_time - timestamps_last_command[fd_out]
            if(delta < INTER_COMMAND_SPACING):
                time_to_sleep = INTER_COMMAND_SPACING - delta
                print("sleeping for %f seconds" % time_to_sleep)
                time.sleep(time_to_sleep)

        s = ''
        for octet in buf:
            s = s + chr(octet)

        fd_out.write(s)
        timestamps_last_command[fd_out] = time.time()
        print("send_display_command: OUT")

PROJECTOR_COMMAND_POWER_ON = [0x43, 0x30, 0x30, 0x0D]
PROJECTOR_COMMAND_POWER_OFF = [0x43, 0x30, 0x31, 0x0D]


if __name__ == '__main__':
    args = sys.argv

    valid_commands = ('ON', 'OFF')

    helptext = (
        "Sanyo Display Device script to control the display's power "
        "state via serial.\n\nusage: python3 sanyo_display_device.py [command]"
        " [display_device_type]\n\ncommands:\n\n\t{commands}\n\nserial_device "
        "should be a {usbserial}-serial_device\n\nexample: python3 {filename} "
        "ON FTCY4Z0L"
    ).format(
        usbserial=USB_SERIAL, filename=args[0],
        commands="\n\t".join(valid_commands)
    )

    # Check for sensible arguments to the script.
    command = None
    if len(args) is 3:
        command = args[1].upper()
        display_device_type = args[2]
        display_device = USB_SERIAL + str(display_device_type)
    if command not in valid_commands:
        print(helptext)
        sys.exit()

    # Try and open the serial device -- this can raise an OSError but the
    # message is fairly self-explanatory so we'll just let that bubble up to
    # the user as it is.
    display = Display()
    fd_display = display.open_device(display_device, LINESPEED_DISPLAY)

    # Execute the command.
    if command == 'ON':
        display.send_sequence_to_projector(
            fd_display, PROJECTOR_COMMAND_POWER_ON
        )
    elif command == 'OFF':
        display.send_sequence_to_projector(
            fd_display, PROJECTOR_COMMAND_POWER_OFF
        )
