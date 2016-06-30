"""
module to send arbitrary pump messages.
"""

from decocare.helpers import messages as decocare_messages
from mmeowlink.handlers.stick import Pump
from mmeowlink.link_builder import LinkBuilder
import argcomplete

class BaseMMeowlinkApp(decocare_messages.SendMsgApp):
  """
  Base class used by other apps here
  """
  def configure_radio_params(self, parser):
    parser.add_argument('--radio_type', dest='radio_type', default='subg_rfspy', choices=['mmcommander', 'subg_rfspy', 'rileylink'])
    parser.add_argument('--mmcommander', dest='radio_type', action='store_const', const='mmcommander')
    parser.add_argument('--subg_rfspy', dest='radio_type', action='store_const', const='subg_rfspy')
    parser.add_argument('--rileylink', dest='radio_type', action='store_const', const='rileylink')

    return parser

  def prelude (self, args):
    port = args.port
    builder = LinkBuilder( )
    if port == 'scan':
      port = builder.scan( )
    self.link = link = LinkBuilder().build(args.radio_type, port)
    link.open()
    # get link
    # drain rx buffer
    self.pump = Pump(self.link, args.serial)

    # Early return if we don't want to send any radio comms. Useful from both
    # the command line and for MMTuneApp
    if args.no_rf_prelude:
      return

    if not args.autoinit:
      if args.init:
        self.pump.power_control(minutes=args.session_life)
    else:
      self.autoinit(args)

    self.sniff_model()

  def postlude(self, args):
    return
