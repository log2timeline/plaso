# -*- coding: utf-8 -*-
"""Plist parser plugin for Apple iOS WiFi Known Networks plist files.

The plist contains information about WiFi networks the device has connected to.
"""

from dfdatetime import posix_time as dfdatetime_posix_time
from plaso.containers import events
from plaso.parsers import plist
from plaso.parsers.plist_plugins import interface


class IOSWiFiKnownNetworksEventData(events.EventData):
    """Apple iOS WiFi Known Networks event data.

    Attributes:
        ssid (str): SSID of the WiFi network.
        added_at (dfdatetime.DateTimeValues): date the network was added.
        last_associated (dfdatetime.DateTimeValues): date the network was last associated.
        bssid (str): BSSID of the WiFi network.
        channel (int): Channel used by the WiFi network.
    """

    DATA_TYPE = 'ios:wifi:known_networks:knowing'

    def __init__(self):
        """Initializes event data."""
        super(IOSWiFiKnownNetworksEventData, self).__init__(data_type=self.DATA_TYPE)
        self.ssid = None
        self.added_at = None
        self.last_associated = None
        self.bssid = None
        self.channel = None


class IOSWiFiKnownNetworksPlistPlugin(interface.PlistPlugin):
    """Plist parser plugin for Apple iOS WiFi Known Networks plist files."""

    NAME = 'ios_wifi_known_networks'
    DATA_FORMAT = 'Apple iOS WiFi Known Networks plist file'

    PLIST_PATH_FILTERS = frozenset([
        interface.PlistPathFilter('com.apple.wifi.known-networks.plist')])

    PLIST_KEYS = frozenset([])


    def _ParsePlist(self, parser_mediator, match=None, top_level=None, **unused_kwargs):
        print(f"Top-level keys in plist: {list(top_level.keys())}")
        """Extract WiFi known network entries.

        Args:
            parser_mediator (ParserMediator): mediates interactions between parsers
                and other components, such as storage and dfVFS.
            match (Optional[dict[str: object]]): keys extracted from PLIST_KEYS.
            top_level (Optional[dict[str: object]]): entire plist file.
        """
        for ssid_key, ssid_data in top_level.items():
            event_data = IOSWiFiKnownNetworksEventData()
            event_data.ssid = ssid_key

            added_at = ssid_data.get('AddedAt')
            if added_at:
                event_data.added_at = dfdatetime_posix_time.PosixTime(
                    timestamp=added_at.timestamp())

            bssid_list = ssid_data.get('BSSList', [])
            print(f"BSSList contains {len(bssid_list)} entries.")
            for bssid_data in bssid_list:
                event_data.bssid = bssid_data.get('BSSID')
                event_data.channel = bssid_data.get('Channel')

                last_associated = bssid_data.get('LastAssociatedAt')
                if last_associated:
                    event_data.last_associated = dfdatetime_posix_time.PosixTime(
                        timestamp=last_associated.timestamp())

                parser_mediator.ProduceEventData(event_data)


plist.PlistParser.RegisterPlugin(IOSWiFiKnownNetworksPlistPlugin)

