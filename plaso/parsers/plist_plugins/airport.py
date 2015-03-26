# -*- coding: utf-8 -*-
"""This file contains the airport plist plugin in Plaso."""

from plaso.events import plist_event
from plaso.parsers import plist
from plaso.parsers.plist_plugins import interface


__author__ = 'Joaquin Moreno Garijo (Joaquin.MorenoGarijo.2013@live.rhul.ac.uk)'


class AirportPlugin(interface.PlistPlugin):
  """Plist plugin that extracts WiFi information."""

  NAME = 'plist_airport'
  DESCRIPTION = u'Parser for Airport plist files.'

  PLIST_PATH = 'com.apple.airport.preferences.plist'
  PLIST_KEYS = frozenset(['RememberedNetworks'])

  def GetEntries(self, parser_mediator, match=None, **unused_kwargs):
    """Extracts relevant Airport entries.

    Args:
      parser_mediator: A parser mediator object (instance of ParserMediator).
      match: Optional dictionary containing keys extracted from PLIST_KEYS.
             The default is None.
    """
    for wifi in match['RememberedNetworks']:
      description = (
          u'[WiFi] Connected to network: <{0:s}> using security {1:s}').format(
              wifi['SSIDString'], wifi['SecurityType'])
      event_object = plist_event.PlistEvent(
          u'/RememberedNetworks', u'item', wifi['LastConnected'], description)
      parser_mediator.ProduceEvent(event_object)


plist.PlistParser.RegisterPlugin(AirportPlugin)
