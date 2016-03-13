from datetime import datetime

from .. hex_handling import hexify
from .. exceptions import CommsException, TimeoutException

from mmeowlink_app import MMeowlinkApp

class RfDumpApp(MMeowlinkApp):
  """
  Tune radio automatically
  """
  def customize_parser(self, parser):
    return self.configure_radio_parser(parser)

  def prelude(self, args):
    # When running mmtune, we don't want the code to try and send
    # prelude packets or auto-init the pump, since they duplicate what
    # we are about to do
    args.no_rf_prelude = True

    super(RfDumpApp, self).prelude(args)

  def main(self, args):
    while True:
      try:
        resp = self.link.get_packet(timeout=1)
        ts = datetime.now()
        print "%s %d db - %s" % (ts, resp['rssi'], hexify(resp['data']).upper())
      except CommsException as e:
        print "CommsException: %s" % e
      except TimeoutException:
        pass
