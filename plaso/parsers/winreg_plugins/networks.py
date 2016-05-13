# -*- coding: utf-8 -*-
"""This file contains the NetworkList registry plugin."""

import binascii

from plaso.containers import windows_events
from plaso.lib import eventdata
from plaso.parsers import winreg
from plaso.parsers.winreg_plugins import interface


class NetworksPlugin(interface.WindowsRegistryPlugin):
  """Windows Registry plugin for parsing the NetworkList key."""

  NAME = u'networks'
  DESCRIPTION = u'Parser for NetworkList data.'

  FILTERS = frozenset([
      interface.WindowsRegistryKeyPathFilter(
          u'HKEY_LOCAL_MACHINE\\Software\\Microsoft\\Windows NT\\CurrentVersion'
          u'\\NetworkList')])

  _CONNECTION_TYPE = {
      0x06: u'Wired',
      0x17: u'3g',
      0x47: u'Wireless'}

  def _GetNetworkInfo(self, signatures_key):
    """Retrieves the network info within the signatures subkey.

    Args:
      signatures_key: A Windows Registry key
                      (instance of dfwinreg.WinRegistryKey).

    Returns:
      A dictionary containing tuples (default_gateway_mac, dns_suffix) hashed
      by profile guid.
    """
    network_info = {}
    for category in signatures_key.GetSubkeys():
      for signature in category.GetSubkeys():
        profile_guid_value = signature.GetValueByName(u'ProfileGuid')
        if profile_guid_value:
          profile_guid = profile_guid_value.GetDataAsObject()
        else:
          continue

        default_gateway_mac_value = signature.GetValueByName(
            u'DefaultGatewayMac')
        if default_gateway_mac_value:
          default_gateway_mac = default_gateway_mac_value.GetDataAsObject()
          default_gateway_mac = u':'.join(
              map(binascii.hexlify, default_gateway_mac))
        else:
          default_gateway_mac = None

        dns_suffix_value = signature.GetValueByName(u'DnsSuffix')
        if dns_suffix_value:
          dns_suffix = dns_suffix_value.GetDataAsObject()
        else:
          dns_suffix = None

        network_info[profile_guid] = (default_gateway_mac, dns_suffix)

    return network_info

  def GetEntries(self, parser_mediator, registry_key, **kwargs):
    """Retrieves information from the NetworkList registry key.

    Args:
      parser_mediator: A parser mediator object (instance of ParserMediator).
      registry_key: A Windows Registry key (instance of
                    dfwinreg.WinRegistryKey).
    """
    network_info = {}
    signatures = registry_key.GetSubkeyByName(u'Signatures')
    if signatures:
      network_info = self._GetNetworkInfo(signatures)

    profiles = registry_key.GetSubkeyByName(u'Profiles')
    if not profiles:
      return

    for subkey in profiles.GetSubkeys():
      default_gateway_mac, dns_suffix = network_info.get(
          subkey.name, (None, None))

      ssid_value = subkey.GetValueByName(u'ProfileName')
      if ssid_value:
        ssid = ssid_value.GetDataAsObject()
      else:
        ssid = None

      description_value = subkey.GetValueByName(u'Description')
      if description_value:
        description = description_value.GetDataAsObject()
      else:
        description = None

      connection_type_value = subkey.GetValueByName(u'NameType')
      if connection_type_value:
        connection_type = connection_type_value.GetDataAsObject()
        connection_type = self._CONNECTION_TYPE.get(
            connection_type, u'unknown')
      else:
        connection_type = None

      date_created = subkey.GetValueByName(u'DateCreated')
      if date_created:
        event_object = windows_events.WindowsRegistryNetworkEvent(
            date_created.GetDataAsObject(),
            eventdata.EventTimestamp.CREATION_TIME,
            ssid, description, connection_type, default_gateway_mac,
            dns_suffix)
        parser_mediator.ProduceEvent(event_object)

      date_last_connected = subkey.GetValueByName(u'DateLastConnected')
      if date_last_connected:
        event_object = windows_events.WindowsRegistryNetworkEvent(
            date_last_connected.GetDataAsObject(),
            eventdata.EventTimestamp.LAST_CONNECTED,
            ssid, description, connection_type, default_gateway_mac,
            dns_suffix)
        parser_mediator.ProduceEvent(event_object)


winreg.WinRegistryParser.RegisterPlugin(NetworksPlugin)
