from mmeowlink_app import MMeowlinkApp

class SendMsgApp(MMeowlinkApp):
  """
  mmeowlink adapter to decocare's SendMsgApp. All actual implementation details
  are handled in MMeowlinkApp and messages in decocare.helpers
  """
  def customize_parser(self, parser):
    return super(SendMsgApp, self).customize_parser(
      self.configure_radio_parser(parser)
    )
