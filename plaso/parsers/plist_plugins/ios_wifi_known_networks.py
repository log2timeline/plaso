# -*- coding: utf-8 -*-
"""Plist parser plugin for Apple iOS WiFi Known Networks plist files.

The plist contains information about WiFi networks the device has connected to.
"""

from plaso.containers import events
from plaso.parsers import plist
from plaso.parsers.plist_plugins import interface


class IOSWiFiKnownNetworksEventData(events.EventData):
  """Apple iOS WiFi Known Networks event data.

  Attributes:
    added_time (dfdatetime.DateTimeValues): date the network was added.
    bssid (str): BSSID of the WiFi network.
    channel (int): Channel used by the WiFi network.
    last_associated_time (dfdatetime.DateTimeValues): date the network was last
        associated.
    ssid (str): SSID of the WiFi network.
  """

  DATA_TYPE = 'ios:wifi:known_networks:entry'

  def __init__(self):
    """Initializes event data."""
    super(IOSWiFiKnownNetworksEventData, self).__init__(
        data_type=self.DATA_TYPE)
    self.added_time = None
    self.bssid = None
    self.channel = None
    self.last_associated_time = None
    self.ssid = None


class IOSWiFiKnownNetworksPlistPlugin(interface.PlistPlugin):
  """Plist parser plugin for Apple iOS WiFi Known Networks plist files."""

  NAME = 'ios_wifi_known_networks'
  DATA_FORMAT = 'Apple iOS WiFi Known Networks plist file'

  PLIST_PATH_FILTERS = frozenset([
      interface.PlistPathFilter('com.apple.wifi.known-networks.plist')])

  PLIST_KEYS = frozenset([])

  def _ParsePlist(
      self, parser_mediator, match=None, top_level=None, **unused_kwargs):
    """Extract WiFi known network entries.

    Args:
        parser_mediator (ParserMediator): mediates interactions between parsers
            and other components, such as storage and dfVFS.
        match (Optional[dict[str: object]]): keys extracted from PLIST_KEYS.
        top_level (Optional[dict[str: object]]): entire plist file.
    """
    for network_values in top_level.values():
      event_data = IOSWiFiKnownNetworksEventData()
      event_data.added_time = self._GetDateTimeValueFromPlistKey(
          network_values, 'AddedAt')
      # TODO: add support for JoinedByUserAt
      # TODO: add support for JoinedBySystemAt
      # TODO: add support for UpdatedAt
      event_data.ssid = network_values.get('SSID').decode('utf8')

      for bssid_data in network_values.get('BSSList', []):
        event_data.bssid = bssid_data.get('BSSID')
        event_data.channel = bssid_data.get('Channel')
        event_data.last_associated_time = self._GetDateTimeValueFromPlistKey(
            bssid_data, 'LastAssociatedAt')

        parser_mediator.ProduceEventData(event_data)

      # TODO: add support for __OSSpecific__ knownBSSUpdatedDate,
      # prevJoined and WiFiNetworkPasswordModificationDate


plist.PlistParser.RegisterPlugin(IOSWiFiKnownNetworksPlistPlugin)
