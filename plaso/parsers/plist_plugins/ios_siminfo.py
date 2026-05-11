"""Plist parser plugin for Apple iOS SIM information plist files."""

from dfdatetime import posix_time as dfdatetime_posix_time

from plaso.containers import events
from plaso.parsers.plist_plugins import interface
from plaso.parsers.plist import PlistParser


class IOSSIMInfoEventData(events.EventData):
  """Apple iOS SIM information event data.

  Attributes:
    cell_broadcast_version (str): Cell broadcast version.
    eap_aka_enabled (bool): value to indicate EAP-AKA is enabled.
    label_identifier (str): label identifier.
    last_used_time (dfdatetime.DateTimeValues): date and time the SIM was last
        used.
    phone_number (str): phone number.
    sim_type (str): type of SIM
  """

  DATA_TYPE = 'ios:sim:info'

  def __init__(self):
    """Initializes event data."""
    super().__init__(data_type=self.DATA_TYPE)
    self.cell_broadcast_version = None
    self.eap_aka_enabled = None
    self.label_identifier = None
    self.last_used_time = None
    self.phone_number = None
    self.sim_type = None


class IOSSIMInfoPlugin(interface.PlistPlugin):
  """Plist parser plugin for Apple iOS SIM information plist files."""

  NAME = 'ios_siminfo'
  DATA_FORMAT = 'iOS SIM Info plist file'

  PLIST_PATH_FILTERS = frozenset([
      interface.PlistPathFilter('com.apple.commcenter.data.plist')])

  PLIST_KEYS = frozenset([
      'PersonalWallet', 'PersonalitySlots', 'pw_ver',
      'unique-sim-label-store'])

  # pylint: disable=arguments-differ
  def _ParsePlist(self, parser_mediator, match=None, **unused_kwargs):
    """Extract SIM information entries.

    Args:
      parser_mediator (ParserMediator): mediates interactions between parsers
          and other components, such as storage and dfVFS.
      match (Optional[dict[str: object]]): keys extracted from PLIST_KEYS.
    """
    personal_wallet = match.get('PersonalWallet', {})
    for _, wallet_item in personal_wallet.items():
      info = wallet_item.get('info', {})
      timestamp = timestamp=info.get('ts')

      event_data = IOSSIMInfoEventData()
      event_data.cell_broadcast_version = info.get('cb_ver')
      event_data.eap_aka_enabled = info.get('eap_aka')
      event_data.label_identifier = info.get('label-id')
      # Mobile Directory Number.
      event_data.phone_number = info.get('mdn')
      event_data.sim_type = info.get('type')

      if timestamp is not None:
        event_data.last_used_time = dfdatetime_posix_time.PosixTime(
            timestamp=timestamp)

      parser_mediator.ProduceEventData(event_data)


PlistParser.RegisterPlugin(IOSSIMInfoPlugin)
