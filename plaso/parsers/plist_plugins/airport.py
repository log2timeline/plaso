# -*- coding: utf-8 -*-
"""Plist parser plugin for Airport plist files."""

from dfdatetime import semantic_time as dfdatetime_semantic_time
from dfdatetime import time_elements as dfdatetime_time_elements

from plaso.containers import plist_event
from plaso.containers import time_events
from plaso.lib import definitions
from plaso.parsers import plist
from plaso.parsers.plist_plugins import interface


class AirportPlugin(interface.PlistPlugin):
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
          and other components, such as storage and dfvfs.
      match (Optional[dict[str: object]]): keys extracted from PLIST_KEYS.
    """
    if 'RememberedNetworks' not in match:
      return

    for wifi in match['RememberedNetworks']:
      ssid = wifi.get('SSIDString', 'UNKNOWN_SSID')
      security_type = wifi.get('SecurityType', 'UNKNOWN_SECURITY_TYPE')

      event_data = plist_event.PlistTimeEventData()
      event_data.desc = (
          '[WiFi] Connected to network: <{0:s}> using security {1:s}').format(
              ssid, security_type)
      event_data.key = 'item'
      event_data.root = '/RememberedNetworks'

      datetime_value = wifi.get('LastConnected', None)
      if datetime_value:
        date_time = dfdatetime_time_elements.TimeElementsInMicroseconds()
        date_time.CopyFromDatetime(datetime_value)
      else:
        date_time = dfdatetime_semantic_time.NotSet()

      event = time_events.DateTimeValuesEvent(
          date_time, definitions.TIME_DESCRIPTION_WRITTEN)
      parser_mediator.ProduceEventWithEventData(event, event_data)


plist.PlistParser.RegisterPlugin(AirportPlugin)
