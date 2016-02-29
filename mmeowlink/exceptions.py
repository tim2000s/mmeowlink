class CommsException(Exception):
  pass

class MMCommanderNotWriteable(Exception):
  pass

class SubgRfspyVersionNotSupported (Exception):
  pass

class PortNotFound(Exception):
  pass

class UnknownLinkType (Exception):
  pass

class UnableToCommunicateWithRadio (Exception):
  pass
