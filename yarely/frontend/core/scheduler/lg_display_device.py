import logging
import serial
import sys
import re
import time

from struct import unpack


log = logging.getLogger(__name__)


# MACHINE SETTINGS
USB_SERIAL = '/dev/tty.usbserial-'


# DISPLAY SERIAL SETTINGS
BAUDRATE = 9600
PARITY = serial.PARITY_NONE
STOPBITS = serial.STOPBITS_ONE
BYTESIZE = serial.EIGHTBITS

# DISPLAY POWER STATE COMMANDS
LG_COMMAND_SET_POWER_ON = b'ka 00 01\r'
LG_COMMAND_SET_POWER_OFF = b'ka 00 00\r'
LG_ENQUIRY_POWER_STATUS = b'ka 00 ff\r'

# DISPLAY VOLUME COMMANDS
LG_COMMAND_SET_MUTE_OFF = b'ke 00 01\r'
LG_COMMAND_SET_MUTE_ON = b'ke 00 00\r'
LG_COMMAND_SET_VOLUME = b'kf 00 {}\r'


# DISPLAY POWER STATE RESPONSES
LG_STATE_POWER_REGEX = re.compile(b'a ([0-9][1-9]) OK(0[0-1])x')
LG_STATE_POWER_ON = '01'
LG_STATE_POWER_OFF = '00'

# VALID VOLUME VALUES
LG_MIN_VOLUME = 0
LG_MAX_VOLUME = 64


class LGPublicDisplay(object):
    """
    Compatible with LG displays.
    """

    def __init__(self, port):
        self.serial_connection = self.open_serial(port)

    def open_serial(self, port):
        full_path_to_port = USB_SERIAL + port
        log.debug("Open serial: {full_path_to_port}".format(
            full_path_to_port=full_path_to_port)
        )
        ser = serial.Serial(
            port=full_path_to_port, baudrate=BAUDRATE,
            parity=PARITY, stopbits=STOPBITS, bytesize=BYTESIZE
        )
        log.debug("Opened serial <<<{serial}>>>".format(serial=ser))
        return ser

    def close_serial(self):
        log.debug("Close serial <<<{serial}>>>".format(
            serial=self.serial_connection
        ))
        self.serial_connection.close()

    def _get_volume_code(self, volume_percentage):
        volume = int((LG_MAX_VOLUME / 100.0) * volume_percentage)
        cmd = LG_COMMAND_SET_VOLUME.format(volume)
        log.debug("Volume cmd is {}".format(cmd))
        return cmd

    def _send_raw_cmd(self, cmd):
        log.debug(
            "Send raw cmd <<<{cmd}>>> to <<<{ser}>>>".format(
                cmd=cmd, ser=self.serial_connection
            )
        )
        response = self.serial_connection.write(bytes(cmd))
        log.debug("Response <<<{response}>>>".format(response=response))

    def _read_raw_response(self):
        log.debug("Reading serial...")
        # Returns output in bytes
        # Sleep for 1 sec to give device time to answer
        time.sleep(1)
        output_list = []
        raw_output = b''
        while self.serial_connection.inWaiting() > 0:
            raw_output += self.serial_connection.read(1)
        return raw_output

    def _turn_display_off(self):
        log.info('Turning display off...')
        self._send_raw_cmd(LG_COMMAND_SET_POWER_OFF)

    def get_power_status(self):
        log.debug("Requesting display power status")
        self._send_raw_cmd(LG_ENQUIRY_POWER_STATUS)
        response = self._read_raw_response()
        logging.debug('RESPONSE:' + str(response))

        power_state = None
        match = LG_STATE_POWER_REGEX.match(response)
        try:
            (set_id, power_state) = match.groups()
        except (AttributeError, ValueError):
            pass

        if power_state == LG_STATE_POWER_ON:
            log.info('Display is on.')
            return "IS_ON"
        elif power_state == LG_STATE_POWER_OFF:
            log.info("Display is off.")
            return "IS_OFF"

        log.warning('Display is not responding.')
        return "UNKNOWN_STATE"


if __name__ == '__main__':
    args = sys.argv

    valid_commands = (
        'ON', 'OFF', 'GET_POWER_STATUS', 'MUTE_OFF', 'MUTE_ON', 'MUTE', 'VOLUME_UP', 'VOLUME_DOWN'
    )

    helptext = (
        "LG Display Device script to control and check the display's power "
        "state via serial.\n\nusage: python3 lg_display_device.py [command] "
        "[serial_device]\n\ncommands:\n\n\t{commands}\n\nserial_device should "
        "be a {usbserial}-serial_device\n\nexample: python3 {filename} ON "
        "FTCY4Z0L"
    ).format(
        usbserial=USB_SERIAL, filename=args[0],
        commands="\n\t".join(valid_commands)
    )

    # Check for sensible arguments to the script.
    command = None
    if len(args) is 3:
        command = args[1].upper()
        serial_device = args[2]
    if command not in valid_commands:
        print(helptext)
        sys.exit()

    # Try and open the serial device -- this can raise an OSError but the
    # message is fairly self-explanatory so we'll just let that bubble up to
    # the user as it is.
    display = LGPublicDisplay(serial_device)

    # Execute the command.
    if command == 'ON':
        display._send_raw_cmd(LG_COMMAND_SET_POWER_ON)
    elif command == 'OFF':
        display._turn_display_off()
    elif command == 'GET_POWER_STATUS':
        print(display.get_power_status())
    elif command in ('MUTE_ON', 'MUTE'):
        display._send_raw_cmd(LG_COMMAND_SET_MUTE_ON)
    elif command == 'MUTE_OFF':
        display._send_raw_cmd(LG_COMMAND_SET_MUTE_OFF)    

    display._read_raw_response()

    # Cleanup the serial device before we exit
    display.close_serial()
