
# Based on decoding-carelink/decocare/link.py

import array
import binascii
import logging
import time

from .. exceptions import SubgRfspyVersionNotSupported, CommsException, TimeoutException
from .. fourbysix import FourBySix
from .. hex_handling import hexify

from serial_interface import SerialInterface
from serial_rf_spy import SerialRfSpy
from subg_rfspy_radio_config import SubgRfspyRadioConfig

io  = logging.getLogger( )
log = io.getChild(__name__)

class SubgRfspyLink(SerialInterface):
  TIMEOUT = 1
  REPETITION_DELAY = 0
  MAX_REPETITION_BATCHSIZE = 250

  # Which version of subg_rfspy do we support?
  SUPPORTED_VERSIONS = ["0.6"]

  RFSPY_ERRORS = {
    0xaa: "Timeout",
    0xbb: "Command Interrupted",
    0xcc: "Zero Data"
  }

  def __init__(self, device, radio_config=None):
    self.timeout = 1
    self.device = device
    self.speed = 19200
    self.radio_config = radio_config

    self.open()
    self.apply_radio_config()

  def check_setup(self):
    self.serial_rf_spy = SerialRfSpy(self.serial)

    self.serial_rf_spy.sync()

    # Check it's a SerialRfSpy device by retrieving the firmware version
    self.serial_rf_spy.send_command(self.serial_rf_spy.CMD_GET_VERSION, timeout=1)
    version = self.serial_rf_spy.get_response(timeout=1).split(' ')[1]

    log.debug('serial_rf_spy Firmare version: %s' % version)

    if version not in self.SUPPORTED_VERSIONS:
      raise SubgRfspyVersionNotSupported("Your subg_rfspy version (%s) is not in the supported version list: %s" % (version, "".join(self.SUPPORTED_VERSIONS)))

  def apply_base_freq(self, freq_mhz):
    self.radio_config.set_base_freq(freq_mhz)

    # Optimisation: don't set all radio registers, just the frequency-related ones:
    for register in ['freq0', 'freq1', 'freq2']:
      self.update_radio(register, self.radio_config.get_config(register))
      time.sleep(1)

  def apply_radio_config(self):
    for register in SubgRfspyRadioConfig.available_registers():
      self.update_radio(register, self.radio_config.get_config(register))

  def update_radio(self, register, value, timeout=1):
    reg = SubgRfspyRadioConfig.REGISTERS[register]["reg"]
    args = chr(reg) + chr(value)
    resp = self.serial_rf_spy.do_command(self.serial_rf_spy.CMD_UPDATE_REGISTER, args, timeout=timeout)

    if len(resp) != 1:
      raise NotImplementedError("Cannot set register %s to 0x%x - received no response" % (register, value))

    if ord(resp) != 1:
      raise NotImplementedError("Cannot set register %s to 0x%x - received response of %i" % (register, id, ord(resp)))

  def write(self, string, repetitions=1, repetition_delay=0, timeout=None):
    rf_spy = self.serial_rf_spy

    remaining_messages = repetitions
    while remaining_messages > 0:
      if remaining_messages < self.MAX_REPETITION_BATCHSIZE:
        transmissions = remaining_messages
      else:
        transmissions = self.MAX_REPETITION_BATCHSIZE
      remaining_messages = remaining_messages - transmissions

      channel = self.radio_config.tx_channel
      encoded = FourBySix.encode(string)
      message = chr(channel) + chr(transmissions - 1) + chr(repetition_delay) + encoded

      print("WRITE: (%s / %d / %s):\n%s" % (channel, transmissions - 1, repetition_delay, hexify(message)))
      rf_spy.do_command(rf_spy.CMD_SEND_PACKET, message, timeout=timeout)

  def get_packet( self, timeout=None ):
    rf_spy = self.serial_rf_spy

    if timeout is None:
      timeout = self.timeout

    timeout_ms = timeout * 1000
    timeout_ms_high = int(timeout_ms / 256)
    timeout_ms_low = int(timeout_ms - (timeout_ms_high * 256))

    channel = self.radio_config.rx_channel
    resp = rf_spy.do_command(SerialRfSpy.CMD_GET_PACKET, chr(channel) + chr(timeout_ms_high) + chr(timeout_ms_low), timeout=timeout + 1)
    # print("GET_PACKET: (Channel:%s / Timeout:%d):\nResp: %s" % (channel, timeout, hexify(resp)))

    if not resp:
      raise CommsException("Did not get a response, or response is too short: %s" % len(resp))

    if self.RFSPY_ERRORS.has_key(resp[0]) and self.RFSPY_ERRORS[ resp[0] ] == "Timeout":
      raise TimeoutException("Timed out receiving data from radio")

    # If the length is less than or equal to 2, then it means we've received an error
    if len(resp) <= 2:
      raise CommsException("Received an error response %s" % self.RFSPY_ERRORS[ resp[0] ])

    decoded = FourBySix.decode(resp[2:])
    # print("DECODED_PACKET:\n%s" % hexify(decoded))

    rssi_dec = resp[0]
    sequence = resp[1]

    rssi_offset = 73
    if rssi_dec >= 128:
      rssi = (( rssi_dec - 256) / 2) - rssi_offset
    else:
      rssi = (rssi_dec / 2) - rssi_offset

    # print("RETURNING: rssi:%d sequence:%d data:%s" % (rssi, sequence, hexify(decoded)))
    return {'rssi':rssi, 'sequence':sequence, 'data':decoded}

  def read( self, timeout=None ):
    return self.get_packet(timeout)['data']
