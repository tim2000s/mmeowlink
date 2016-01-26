from mmeowlink.exceptions import UnknownLinkType

from mmeowlink.vendors.mmcommander_link import MMCommanderLink
from mmeowlink.vendors.subg_rfspy_link import SubgRfspyLink

class LinkBuilder():
  def build(self, radio_type, port, radio_config):
    if radio_type == 'mmcommander':
      implementation = MMCommanderLink
    elif radio_type == 'subg_rfspy':
      implementation = SubgRfspyLink
    else:
      raise UnknownLinkType("Unknown radio type '%s' - check parameters" % radio_type)

    return implementation(port, radio_config=radio_config)
