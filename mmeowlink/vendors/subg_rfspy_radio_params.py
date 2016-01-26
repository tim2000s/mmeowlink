from subg_rfspy_radio_config import SubgRfspyRadioConfig

class SubgRfspyRadioParams():
  @staticmethod
  def add_arguments(parser):
    parser.add_argument('--subg_rfspy_radio_locale', default='usa', choices=['usa', 'worldwide'])
    parser.add_argument('--subg_rfspy_radio_rx_channel', default='0', choices=['0', '1', '2'])
    parser.add_argument('--subg_rfspy_radio_tx_channel', default='0', choices=['0', '1', '2'])

    for register in SubgRfspyRadioConfig.available_registers():
      name = '--subg_rfspy_%s' % register
      parser.add_argument(name)
