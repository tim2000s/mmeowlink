
from decocare import session, lib, commands
from .. packets.rf import Packet

import logging

from decocare import lib

io  = logging.getLogger( )
log = io.getChild(__name__)

class Sender (object):
  STANDARD_RETRY_COUNT = 3
  RETRY_BACKOFF = 1

  sent_params = False
  expected = 64
  def __init__ (self, link):
    self.link = link
    self.frames = [ ]

  def send (self, payload):
    self.link.write(payload)

  def send_params (self):
    command = self.command
    params = self.command.params
    payload = bytearray([len(params)]) + bytearray(params)
    missing = [ ]
    missing = bytearray([0x00]) * (64 - len(params))
    payload = payload + missing
    pkt = Packet.fromCommand(command, payload=payload, serial=command.serial)
    pkt = pkt.update(payload)
    buf = pkt.assemble( )
    self.link.write(buf)
    self.sent_params = True

  def ack (self):
    null = bytearray([0x00])
    pkt = Packet.fromCommand(self.command, payload=null, serial=self.command.serial)
    pkt = pkt._replace(payload=null, op=0x06)
    buf = pkt.assemble( )
    self.link.write(buf)

  def unframe (self, resp):
    if self.expected > 64:
      num, payload = resp.payload[0], resp.payload[1:]
      self.frames.append((num, resp.payload))
      self.ack( )
    else:
      payload = resp.payload[1:]

    self.command.respond(payload)

  def done (self):
    needs_params = self.command.params and len(self.command.params) > 0 or False
    if needs_params and not self.sent_params:
      print("Done? No - needs params and not sent_params")
      return False

    command_done = self.command.done( )
    if command_done:
      print("Done? Yes - Command is done")
    else:
      print("Done? No - command thinks we are not yet finished")
    return command_done

  def respond (self, resp):
    if resp.valid and resp.serial == self.command.serial:
      if resp.op == 0x06:
        # if not self.command.done( ) or (self.command.params and not self.sent_params):
        if not self.done( ):
          return self.command
        else:
          return self.command
      if resp.op == self.command.code:
        # self.command.respond(resp.payload)
        self.unframe(resp)
        if self.done( ):
          return self.command
        else:
          pass

  def wait_for_ack (self, timeout=.500):
    print("wait_for_ack")
    link = self.link

    while not self.done( ):
      print("wait_for_ack Not done")
      buf = link.read( timeout=timeout )

      resp = Packet.fromBuffer(buf)
      if self.responds_to(resp):
        print("wait_for_ack: responds_to")
        if resp.op == 0x06:
          print("wait_for_ack: resp is 0x06")
          return resp

  def responds_to (self, resp):
    print("responds_to: checking valid and serial number")
    return resp.valid and resp.serial == self.command.serial

  def wait_response (self):
    print("wait_response")
    link = self.link
    buf = link.read( )
    resp = Packet.fromBuffer(buf)
    print("packet: %s" % (str(buf).encode('hex')))
    if self.responds_to(resp):
      return resp

  def prelude (self):
    link = self.link
    command = self.command

    self.expected = command.bytesPerRecord * command.maxRecords

    payload = bytearray([0])
    self.pkt = Packet.fromCommand(command, payload=payload, serial=command.serial)
    self.pkt = self.pkt.update(payload)
    buf = self.pkt.assemble( )
    self.send(buf)

  def upload (self):
    # import pdb; pdb.set_trace()
    params = self.command.params

    should_send = len(params) > 0
    if should_send:
      print("upload: should_send")
      self.wait_for_ack( )
      print("upload: sending params")
      self.send_params( )

  def __call__ (self, command):
    self.command = command
    print("__call__ starting command %0xdx (%s)" % (command.code, command.descr))
    print("Starting prelude")
    self.prelude()
    print("Starting upload")
    self.upload()

    print("Waiting for done status")
    while not self.done( ):
      print("Not done")
      resp = self.wait_response( )
      if resp:
        print("Got a resp")
        self.respond(resp)

    print("Done - returning from __call__")
    return command

class Repeater (Sender):

  def __call__ (self, command, repetitions=None, ack_wait_seconds=None, retry_count=None):
    self.command = command

    pkt = Packet.fromCommand(self.command, serial=self.command.serial)
    buf = pkt.assemble( )
    log.info('Sending repeated message %s' % (str(buf).encode('hex')))

    self.link.write(buf, repetitions=repetitions)

    self.wait_for_ack(timeout=ack_wait_seconds)

class Pump (session.Pump):
  STANDARD_RETRY_COUNT = 3
  STANDARD_RETRY_BACKOFF = 1

  def __init__ (self, link, serial):
    self.link = link
    self.serial = serial

  def power_control (self, minutes=None):
    """ Control Pumping """
    log.info('BEGIN POWER CONTROL %s' % self.serial)
    self.command = commands.PowerControl(**dict(minutes=minutes, serial=self.serial))
    repeater = Repeater(self.link)

    repeater(self.command, repetitions=500, ack_wait_seconds=15, retry_count=2)

  def execute (self, command):
    command.serial = self.serial

    sender = Sender(self.link)
    return sender(command)
