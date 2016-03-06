from mmeowlink.mmtune import MMTune

from mmeowlink_app import MMeowlinkApp

class MMTuneApp(MMeowlinkApp):
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

    super(MMTuneApp, self).prelude(args)

  def main(self, args):
    tuner = MMTune(self.link, args.serial)
    output = tuner.run()
    print json.dumps(output, sort_keys=True,indent=4, separators=(',', ': '))
