from mmeowlink.mmtune import MMTune

from mmeowlink_app import MMeowlinkApp

class MMTuneApp(MMeowlinkApp):
  """
  Tune radio automatically
  """
  def customize_parser(self, parser):
    return self.configure_radio_parser(parser)

  def main(self, args):
    tuner = MMTune(link, serial)
    output = tuner.run()
    print json.dumps(output, sort_keys=True,indent=4, separators=(',', ': '))
