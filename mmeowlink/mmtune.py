#!/usr/bin/env python

import sys
from decocare.lib import CRC8
from exceptions import CommsException

from mmeowlink.vendors.subg_rfspy_link import SubgRfspyLink
from mmeowlink.vendors.subg_rfspy_radio_config import SubgRfspyRadioConfig

class MMTune:

  def __init__(self, link, pumpserial):
    self.link = link
    self.radio_config = link.radio_config
    self.scan_range = link.radio_config.get_scan_range()

    self.pumpserial = pumpserial

  def run(self):
    #print "waking..."
    self.wakeup()

    #print "scanning..."
    results = self.scan_over_freq(
      self.scan_range['start'],
      self.scan_range['end'],
      20
    )
    results_sorted = list(reversed(sorted(results, key=lambda x: x[1:])))

    set_freq = scan_range['default']

    if results_sorted[0][1] > 0:
      used_default = False
      set_freq = float(results_sorted[0][0])
    else:
      used_default = True

    self.link.apply_base_freq(set_freq)
    output = {'scanDetails': results, 'setFreq': set_freq, 'usedDefault': used_default}

    return output

  def scan_over_freq(self, start_freq, end_freq, steps):
    step_size = (end_freq - start_freq) / steps
    cur_freq = start_freq
    results = []
    while cur_freq < end_freq:
      print("Setting frequency %f" % cur_freq)
      self.link.apply_base_freq(cur_freq)
      results.append(self.run_trial("%0.3f" % cur_freq))
      cur_freq += step_size
    return results

  def run_trial(self, var):
    sample_size = 5
    success_count = 0
    error_count = 0
    rssi_readings = []
    for i in xrange(sample_size):
      self.send_packet("a7" + self.pumpserial + "8d00") # Get Model
      try:
        packet = self.get_packet(0.080)
        success_count += 1
        rssi_readings.append(packet["rssi"])
      except CommsException:
        error_count += 1
        rssi_readings.append(-99)

    avg_rssi = sum(rssi_readings)/len(rssi_readings)

    #print "%s, %d, rssi:%0.1f" % (var, error_count, avg_rssi)
    return [var, success_count, avg_rssi]

  def send_packet(self, data, tx_count=1, msec_repeat_delay=0):
    buf = bytearray()
    buf.extend(data.decode('hex'))
    buf.extend([CRC8.compute(buf)])
    self.link.write(buf, tx_count, msec_repeat_delay)

  def get_packet(self, timeout=0):
    return self.link.get_packet(timeout)

  def wakeup(self):
    awake = False
    for i in xrange(3):
      self.send_packet("a7" + self.pumpserial + "8d00")
      try:
        packet = self.get_packet(0.08)
        #print "packet = " + str(packet)
      except CommsException:
        packet = None
        #print "No response..."
        pass
      if packet:
        #print "Woke up pump: " + str(packet)
        awake = True
        break

    if awake != True:
      # Pump in free space
      self.link.apply_base_freq(self.scan_range['default'])

      # Send 200 wake-up packets
      self.send_packet("a7" + self.pumpserial + "5d00", 200)
      try:
        wake_ack = self.get_packet(9) # wait 9 s for response
      except CommsException:
        wake_ack = None
        #print "No response..."
        pass
