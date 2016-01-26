from mmeowlink.exceptions import UnknownLinkType
from mmeowlink.vendors.subg_rfspy_radio_config import SubgRfspyRadioConfig

class RadioConfigBuilder():

  @staticmethod
  def build(radio_type, args):
    if radio_type == 'mmcommander':
      radio_config = None
    elif args.radio_type == 'subg_rfspy':
      radio_config = SubgRfspyRadioConfig()

      # The radio locale is set first, and then individual items are set as
      # overrides, if supplied
      if args.subg_rfspy_radio_locale:
        method_name = "locale_%s" % args.subg_rfspy_radio_locale
        getattr(radio_config, method_name)()

      # Channels are handled separately from other parameters, since they are
      # used at every send and every receive, rather than necessarily in the
      # base radio settings. However, there is an overall channel
      if args.subg_rfspy_radio_tx_channel:
        radio_config.tx_channel = int(args.subg_rfspy_radio_tx_channel)

      if args.subg_rfspy_radio_rx_channel:
        radio_config.rx_channel = int(args.subg_rfspy_radio_rx_channel)

      # Now try and set any additional radio parameters dynamically, based
      # on the list of configured registers
      for register in SubgRfspyRadioConfig.available_registers():
        arg_name = "subg_rfspy_%s" % register

        val = getattr(args, arg_name)
        if val:
          radio_config.set_register(register, int(val, 16))
    else:
      raise UnknownLinkType("Unknown radio type when building radio config '%s' - check parameters" % radio_type)

    return radio_config
