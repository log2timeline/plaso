# -*- coding: utf-8 -*-
"""Plist parser plugin for MacOS Airport plist files."""

from dfdatetime import semantic_time as dfdatetime_semantic_time
from dfdatetime import time_elements as dfdatetime_time_elements

from plaso.containers import events
from plaso.containers import time_events
from plaso.lib import definitions
from plaso.parsers import plist
from plaso.parsers.plist_plugins import interface


class MacOSAirportEventData(events.EventData):
  """MacOS airport event data.

  Attributes:
    security_type (str): WiFI security type.
    ssid (str): WiFI SSID.
  """

  DATA_TYPE = 'macos:airport:entry'

  def __init__(self):
    """Initializes event data."""
    super(MacOSAirportEventData, self).__init__(data_type=self.DATA_TYPE)
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
      event_data.security_type = plist_key.get('SecurityType', None)
      event_data.ssid = plist_key.get('SSIDString', None)

      datetime_value = plist_key.get('LastConnected', None)
      if not datetime_value:
        date_time = dfdatetime_semantic_time.NotSet()
      else:
        date_time = dfdatetime_time_elements.TimeElements()
        date_time.CopyFromDatetime(datetime_value)

      event = time_events.DateTimeValuesEvent(
          date_time, definitions.TIME_DESCRIPTION_WRITTEN)
      parser_mediator.ProduceEventWithEventData(event, event_data)


plist.PlistParser.RegisterPlugin(MacOSAirportPlistPlugin)
