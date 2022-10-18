# -*- coding: utf-8 -*-
"""This file contains the NetworkList Registry plugin."""

import os

from dfdatetime import systemtime as dfdatetime_systemtime

from plaso.containers import events
from plaso.lib import dtfabric_helper
from plaso.lib import errors
from plaso.parsers import winreg_parser
from plaso.parsers.winreg_plugins import interface


class WindowsRegistryNetworkListEventData(events.EventData):
  """Windows NetworkList event data.

  Attributes:
    connection_type (int): type of connection.
    creation_time (dfdatetime.DateTimeValues): entry creation date and time.
    default_gateway_mac (str): MAC address for the default gateway.
    description (str): description of the wireless connection.
    dns_suffix (str): DNS suffix.
    last_connected_time (dfdatetime.DateTimeValues): last connected date and
        time.
    ssid (str): SSID of the connection.
  """

  DATA_TYPE = 'windows:registry:network'

  def __init__(self):
    """Initializes event data."""
    super(WindowsRegistryNetworkListEventData, self).__init__(
        data_type=self.DATA_TYPE)
    self.connection_type = None
    self.creation_time = None
    self.default_gateway_mac = None
    self.description = None
    self.dns_suffix = None
    self.last_connected_time = None
    self.ssid = None


class NetworksWindowsRegistryPlugin(
    interface.WindowsRegistryPlugin, dtfabric_helper.DtFabricHelper):
  """Windows Registry plugin for parsing the NetworkList key."""

  NAME = 'networks'
  DATA_FORMAT = 'Windows networks (NetworkList) Registry data'

  FILTERS = frozenset([
      interface.WindowsRegistryKeyPathFilter(
          'HKEY_LOCAL_MACHINE\\Software\\Microsoft\\Windows NT\\CurrentVersion'
          '\\NetworkList')])

  _DEFINITION_FILE = os.path.join(
      os.path.dirname(__file__), 'systemtime.yaml')

  _EMPTY_SYSTEM_TIME_TUPLE = (0, 0, 0, 0, 0, 0, 0, 0)

  def _GetNetworkInfo(self, signatures_key):
    """Retrieves the network info within the signatures subkey.

    Args:
      signatures_key (dfwinreg.WinRegistryKey): a Windows Registry key.

    Returns:
      dict[str, tuple]: a tuple of default_gateway_mac and dns_suffix per
          profile identifier (GUID).
    """
    network_info = {}
    for category in signatures_key.GetSubkeys():
      for signature in category.GetSubkeys():
        profile_guid_value = signature.GetValueByName('ProfileGuid')
        if profile_guid_value:
          profile_guid = profile_guid_value.GetDataAsObject()
        else:
          continue

        default_gateway_mac_value = signature.GetValueByName(
            'DefaultGatewayMac')
        if default_gateway_mac_value:
          default_gateway_mac = ':'.join([
              '{0:02x}'.format(octet)
              for octet in bytearray(default_gateway_mac_value.data)])
        else:
          default_gateway_mac = None

        dns_suffix_value = signature.GetValueByName('DnsSuffix')
        if dns_suffix_value:
          dns_suffix = dns_suffix_value.GetDataAsObject()
        else:
          dns_suffix = None

        network_info[profile_guid] = (default_gateway_mac, dns_suffix)

    return network_info

  def _ParseSystemTime(self, parser_mediator, registry_key, value_name):
    """Parses a SYSTEMTIME date and time value from a byte stream.

    Args:
      parser_mediator (ParserMediator): mediates interactions between parsers
          and other components, such as storage and dfVFS.
      registry_key (dfwinreg.WinRegistryKey): Windows Registry key.
      value_name (str): name of the value to retrieve.

    Returns:
      dfdatetime.Systemtime: SYSTEMTIME date and time value or None if no
          value is set.

    Raises:
      ParseError: if the SYSTEMTIME could not be parsed.
    """
    registry_value = registry_key.GetValueByName(value_name)
    if not registry_value:
      return None

    systemtime_map = self._GetDataTypeMap('systemtime')

    try:
      systemtime = self._ReadStructureFromByteStream(
          registry_value.data, 0, systemtime_map)
    except (ValueError, errors.ParseError) as exception:
      parser_mediator.ProduceExtractionWarning(
          'Unable to parse SYSTEMTIME in value: {0:s} with error: {1!s}'.format(
              value_name, exception))
      return None

    system_time_tuple = (
        systemtime.year, systemtime.month, systemtime.weekday,
        systemtime.day_of_month, systemtime.hours, systemtime.minutes,
        systemtime.seconds, systemtime.milliseconds)

    if system_time_tuple == self._EMPTY_SYSTEM_TIME_TUPLE:
      return None

    try:
      return dfdatetime_systemtime.Systemtime(
          system_time_tuple=system_time_tuple)

    except ValueError:
      parser_mediator.ProduceExtractionWarning(
          'Invalid SYSTEMTIME value: {0!s} in value: {1:s}'.format(
              system_time_tuple, value_name))
      return None

  def ExtractEvents(self, parser_mediator, registry_key, **kwargs):
    """Extracts events from a Windows Registry key.

    Args:
      parser_mediator (ParserMediator): mediates interactions between parsers
          and other components, such as storage and dfVFS.
      registry_key (dfwinreg.WinRegistryKey): Windows Registry key.
    """
    network_info = {}
    signatures = registry_key.GetSubkeyByName('Signatures')
    if signatures:
      network_info = self._GetNetworkInfo(signatures)

    profiles = registry_key.GetSubkeyByName('Profiles')
    if profiles:
      for subkey in profiles.GetSubkeys():
        default_gateway_mac, dns_suffix = network_info.get(
            subkey.name, (None, None))

        event_data = WindowsRegistryNetworkListEventData()
        event_data.connection_type = self._GetValueFromKey(subkey, 'NameType')
        event_data.creation_time = self._ParseSystemTime(
            parser_mediator, subkey, 'DateCreated')
        event_data.default_gateway_mac = default_gateway_mac
        event_data.description = self._GetValueFromKey(subkey, 'Description')
        event_data.dns_suffix = dns_suffix
        event_data.last_connected_time = self._ParseSystemTime(
            parser_mediator, subkey, 'DateLastConnected')
        event_data.ssid = self._GetValueFromKey(subkey, 'ProfileName')

        parser_mediator.ProduceEventData(event_data)


winreg_parser.WinRegistryParser.RegisterPlugin(NetworksWindowsRegistryPlugin)
