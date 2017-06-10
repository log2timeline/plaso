# -*- coding: utf-8 -*-
"""Airport plist plugin."""

from dfdatetime import posix_time as dfdatetime_posix_time
from dfdatetime import semantic_time as dfdatetime_semantic_time

from plaso.containers import plist_event
from plaso.containers import time_events
from plaso.lib import definitions
from plaso.lib import timelib
from plaso.parsers import plist
from plaso.parsers.plist_plugins import interface


__author__ = 'Joaquin Moreno Garijo (Joaquin.MorenoGarijo.2013@live.rhul.ac.uk)'


class AirportPlugin(interface.PlistPlugin):
  """Plist plugin that extracts WiFi information."""

  NAME = u'airport'
  DESCRIPTION = u'Parser for Airport plist files.'

  PLIST_PATH = u'com.apple.airport.preferences.plist'
  PLIST_KEYS = frozenset([u'RememberedNetworks'])

  def GetEntries(self, parser_mediator, match=None, **unused_kwargs):
    """Extracts relevant Airport entries.

    Args:
      parser_mediator (ParserMediator): mediates interactions between parsers
          and other components, such as storage and dfvfs.
      match (Optional[dict[str: object]]): keys extracted from PLIST_KEYS.
    """
    if u'RememberedNetworks' not in match:
      return

    for wifi in match[u'RememberedNetworks']:
      ssid = wifi.get(u'SSIDString', u'UNKNOWN_SSID')
      security_type = wifi.get(u'SecurityType', u'UNKNOWN_SECURITY_TYPE')

      event_data = plist_event.PlistTimeEventData()
      event_data.desc = (
          u'[WiFi] Connected to network: <{0:s}> using security {1:s}').format(
              ssid, security_type)
      event_data.key = u'item'
      event_data.root = u'/RememberedNetworks'

      datetime_value = wifi.get(u'LastConnected', None)
      if datetime_value:
        timestamp = timelib.Timestamp.FromPythonDatetime(datetime_value)
        date_time = dfdatetime_posix_time.PosixTimeInMicroseconds(
            timestamp=timestamp)
        event = time_events.DateTimeValuesEvent(
            date_time, definitions.TIME_DESCRIPTION_WRITTEN)
      else:
        date_time = dfdatetime_semantic_time.SemanticTime(u'Not set')
        event = time_events.DateTimeValuesEvent(
            date_time, definitions.TIME_DESCRIPTION_NOT_A_TIME)

      parser_mediator.ProduceEventWithEventData(event, event_data)


plist.PlistParser.RegisterPlugin(AirportPlugin)
