# -*- coding: utf-8 -*-
"""This file contains the airport plist plugin in Plaso."""

from plaso.containers import plist_event
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
      parser_mediator: A parser mediator object (instance of ParserMediator).
      match: Optional dictionary containing keys extracted from PLIST_KEYS.
    """
    if u'RememberedNetworks' not in match:
      return

    for wifi in match[u'RememberedNetworks']:
      description = (
          u'[WiFi] Connected to network: <{0:s}> using security {1:s}').format(
              wifi.get(u'SSIDString', u'UNKNOWN_SSID'),
              wifi.get(u'SecurityType', u'UNKNOWN_SECURITY_TYPE'))
      event_object = plist_event.PlistEvent(
          u'/RememberedNetworks', u'item', wifi.get(u'LastConnected', 0),
          description)
      parser_mediator.ProduceEvent(event_object)


plist.PlistParser.RegisterPlugin(AirportPlugin)
