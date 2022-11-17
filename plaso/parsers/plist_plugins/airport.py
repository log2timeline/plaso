# -*- coding: utf-8 -*-
"""Plist parser plugin for MacOS Airport plist files."""

from plaso.containers import events
from plaso.parsers import plist
from plaso.parsers.plist_plugins import interface


class MacOSAirportEventData(events.EventData):
  """MacOS airport event data.

  Attributes:
    last_connected_time (dfdatetime.DateTimeValues): last date and time MacOS
        Airport connected to the Wi-Fi network.
    security_type (str): Wi-Fi security type.
    ssid (str): Wi-Fi SSID.
  """

  DATA_TYPE = 'macos:airport:entry'

  def __init__(self):
    """Initializes event data."""
    super(MacOSAirportEventData, self).__init__(data_type=self.DATA_TYPE)
    self.last_connected_time = None
    self.security_type = None
    self.ssid = None


class MacOSAirportPlistPlugin(interface.PlistPlugin):
  """Plist parser plugin for Airport plist files."""

  NAME = 'airport'
  DATA_FORMAT = 'Airport plist file'

  PLIST_PATH_FILTERS = frozenset([
      interface.PlistPathFilter('com.apple.airport.preferences.plist')])

  PLIST_KEYS = frozenset(['RememberedNetworks'])

  # pylint: disable=arguments-differ
  def _ParsePlist(self, parser_mediator, match=None, **unused_kwargs):
    """Extracts relevant Airport entries.

    Args:
      parser_mediator (ParserMediator): mediates interactions between parsers
          and other components, such as storage and dfVFS.
      match (Optional[dict[str: object]]): keys extracted from PLIST_KEYS.
    """
    for plist_key in match.get('RememberedNetworks', []):
      event_data = MacOSAirportEventData()
      event_data.last_connected_time = self._GetDateTimeValueFromPlistKey(
          plist_key, 'LastConnected')
      event_data.security_type = plist_key.get('SecurityType', None)
      event_data.ssid = plist_key.get('SSIDString', None)

      parser_mediator.ProduceEventData(event_data)


plist.PlistParser.RegisterPlugin(MacOSAirportPlistPlugin)
