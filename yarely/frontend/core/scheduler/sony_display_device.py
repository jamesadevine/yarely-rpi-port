import logging
import serial
import sys
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

# DISPLAY COMMANDS
SONY_FWD40LX1_FWDS42E1_COMMAND_GET_POWER_ON = [0x8c, 0x00, 0x00, 0x02, 0x01]
SONY_FWD40LX1_FWDS42E1_COMMAND_GET_POWER_OFF = [0x8c, 0x00, 0x00, 0x02, 0x00]

SONY_FWD40LX1_COMMAND_SET_INPUT_INPUT2_RGB = [0x8c, 0x00, 0x01, 0x02, 0x0a]
SONY_FWD40LX1_COMMAND_SET_INPUT_INPUT2_COMPONENT = [
    0x8c, 0x00, 0x01, 0x02, 0x0b]
SONY_FWD40LX1_COMMAND_SET_INPUT_OPTION1_VIDEO = [0x8c, 0x00, 0x01, 0x02, 0x0c]
SONY_FWD40LX1_COMMAND_SET_INPUT_OPTION1_S_VIDEO = [
    0x8c, 0x00, 0x01, 0x02, 0x0d]
SONY_FWD40LX1_COMMAND_SET_INPUT_OPTION1_RGB = [0x8c, 0x00, 0x01, 0x02, 0x0e]
SONY_FWD40LX1_COMMAND_SET_INPUT_OPTION1_COMPONENT = [
    0x8c, 0x00, 0x01, 0x02, 0x0f]
SONY_FWD40LX1_COMMAND_SET_INPUT_OPTION2_VIDEO = [0x8c, 0x00, 0x01, 0x02, 0x10]
SONY_FWD40LX1_COMMAND_SET_INPUT_OPTION2_S_VIDEO = [
    0x8c, 0x00, 0x01, 0x02, 0x11]
SONY_FWD40LX1_COMMAND_SET_INPUT_OPTION2_RGB = [0x8c, 0x00, 0x01, 0x02, 0x12]
SONY_FWD40LX1_COMMAND_SET_INPUT_OPTION2_COMPONENT = [
    0x8c, 0x00, 0x01, 0x02, 0x13]
SONY_FWD40LX1_COMMAND_SET_INPUT_INPUT1_DVI = [0x8c, 0x00, 0x01, 0x02, 0x20]
SONY_FWD40LX1_COMMAND_GET_INPUT_STATUS = [0x83, 0x00, 0x01, 0xff, 0xff]
SONY_FWD40LX1_COMMAND_SET_MUTE_OFF = [0x8c, 0x00, 0x03, 0x02, 0x00]
SONY_FWD40LX1_COMMAND_SET_MUTE_ON = [0x8c, 0x00, 0x03, 0x02, 0x01]
SONY_FWD40LX1_COMMAND_SET_VOLUME = [0x8c, 0x10, 0x30, 0x02]

SONY_FWD40LX1_FWDS42E1_ENQUIRY_POWER_STATUS = [0x83, 0x00, 0x00, 0xFF, 0xFF]

SONY_FWD40LX1_STATE_POWER_ON = [0x70, 0x00, 0x02, 0x01, 0x73]
SONY_FWD40LX1_STATE_POWER_OFF = [0x70, 0x00, 0x02, 0x00, 0x72]

SONY_FWD40LX1_MIN_VOLUME = 0
SONY_FWD40LX1_MAX_VOLUME = 64


class SonyPublicDisplay(object):
    """
    Compatible with Sony FWD-40LX1 and Sony FWD-S42E1
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
            parity=PARITY, stopbits=STOPBITS,
            bytesize=BYTESIZE)
        log.debug("Opened serial <<<{serial}>>>".format(serial=ser))
        return ser

    def close_serial(self):
        log.debug("Close serial <<<{serial}>>>".format(
            serial=self.serial_connection)
        )
        self.serial_connection.close()

    def _get_volume_code(self, volume_percentage):
        code = SONY_FWD40LX1_COMMAND_SET_VOLUME[:]
        volume = int((SONY_FWD40LX1_MAX_VOLUME / 100.0) * volume_percentage)
        code.append(volume)
        log.debug("Volume code is {volume_code}".format(volume_code=code))
        return code

    def _calculate_checksum(self, buf, length):
        checksum = 0
        for pos in range(length):
            checksum += buf[pos]

        checksum = checksum & ~0xff00
        log.debug("Checksum is %x" % checksum)
        return checksum

    def send_cmd_without_chksum(self, cmd):
        chksum = self._calculate_checksum(cmd, len(cmd))
        cmd_with_chksum = cmd[:]
        cmd_with_chksum.append(chksum)
        self._send_raw_cmd(cmd_with_chksum)

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
        while self.serial_connection.inWaiting() > 0:
            raw_output = self.serial_connection.read(1)
            int_output = unpack('b', raw_output)[0]
            output_list.append(int_output)
        log.debug("Response from serial: {response}".format(
            response=output_list)
        )
        return output_list

    def _turn_display_off(self):
        log.info('Turning display off...')
        self.send_cmd_without_chksum(
            SONY_FWD40LX1_FWDS42E1_COMMAND_GET_POWER_OFF
        )

    def get_power_status(self):
        log.debug("Requesting display power status")
        self.send_cmd_without_chksum(
            SONY_FWD40LX1_FWDS42E1_ENQUIRY_POWER_STATUS
        )
        response = self._read_raw_response()
        if set(response) == set(SONY_FWD40LX1_STATE_POWER_ON):
            log.info('Display is on.')
            return "IS_ON"
        # If no response or response does not match, display is most
        # likely off.
        elif not response:
            log.warning('Display is not responding.')
            return "UNKNOWN_STATE"
        log.info("Display is off.")
        return "IS_OFF"


if __name__ == '__main__':
    args = sys.argv

    valid_commands = ('ON', 'OFF', 'GET_POWER_STATUS')

    helptext = (
        "Sony Display Device script to control and check the display's power "
        "state via serial.\n\nusage: python3 sony_display_device.py [command] "
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
    display = SonyPublicDisplay(serial_device)

    # Execute the command.
    if command == 'ON':
        display.send_cmd_without_chksum(
            SONY_FWD40LX1_FWDS42E1_COMMAND_GET_POWER_ON
        )
    elif command == 'OFF':
        display.send_cmd_without_chksum(
            SONY_FWD40LX1_FWDS42E1_COMMAND_GET_POWER_OFF
        )
    elif command == 'GET_POWER_STATUS':
        print(display.get_power_status())

    # Cleanup the serial device before we exit
    display.close_serial()
