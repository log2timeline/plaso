# -*- coding: utf-8 -*-
"""This file contains the NetworkList registry plugin."""

from __future__ import unicode_literals

import binascii

import construct

from dfdatetime import systemtime as dfdatetime_systemtime

from plaso.containers import events
from plaso.containers import time_events
from plaso.lib import definitions
from plaso.parsers import winreg
from plaso.parsers.winreg_plugins import interface


class WindowsRegistryNetworkEventData(events.EventData):
  """Windows network event data.

  Attributes:
    connection_type (str): type of connection.
    default_gateway_mac (str): MAC address for the default gateway.
    description (str): description of the wireless connection.
    dns_suffix (str): DNS suffix.
    ssid (str): SSID of the connection.
  """

  DATA_TYPE = 'windows:registry:network'

  def __init__(self):
    """Initializes event data."""
    super(WindowsRegistryNetworkEventData, self).__init__(
        data_type=self.DATA_TYPE)
    self.connection_type = None
    self.default_gateway_mac = None
    self.description = None
    self.dns_suffix = None
    self.ssid = None


class NetworksPlugin(interface.WindowsRegistryPlugin):
  """Windows Registry plugin for parsing the NetworkList key."""

  NAME = 'networks'
  DESCRIPTION = 'Parser for NetworkList data.'

  FILTERS = frozenset([
      interface.WindowsRegistryKeyPathFilter(
          'HKEY_LOCAL_MACHINE\\Software\\Microsoft\\Windows NT\\CurrentVersion'
          '\\NetworkList')])

  _CONNECTION_TYPE = {
      0x06: 'Wired',
      0x17: '3g',
      0x47: 'Wireless'}

  _EMPTY_SYSTEM_TIME_TUPLE = (0, 0, 0, 0, 0, 0, 0, 0)

  _SYSTEMTIME_STRUCT = construct.Struct(
      'systemtime',
      construct.ULInt16('year'),
      construct.ULInt16('month'),
      construct.ULInt16('day_of_week'),
      construct.ULInt16('day_of_month'),
      construct.ULInt16('hours'),
      construct.ULInt16('minutes'),
      construct.ULInt16('seconds'),
      construct.ULInt16('milliseconds'))

  def _GetNetworkInfo(self, signatures_key):
    """Retrieves the network info within the signatures subkey.

    Args:
      signatures_key (dfwinreg.WinRegistryKey): a Windows Registry key.

    Returns:
      A dictionary containing tuples (default_gateway_mac, dns_suffix) hashed
      by profile guid.
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
          default_gateway_mac = default_gateway_mac_value.GetDataAsObject()
          default_gateway_mac = ':'.join(
              map(binascii.hexlify, default_gateway_mac))
        else:
          default_gateway_mac = None

        dns_suffix_value = signature.GetValueByName('DnsSuffix')
        if dns_suffix_value:
          dns_suffix = dns_suffix_value.GetDataAsObject()
        else:
          dns_suffix = None

        network_info[profile_guid] = (default_gateway_mac, dns_suffix)

    return network_info

  def ExtractEvents(self, parser_mediator, registry_key, **kwargs):
    """Extracts events from a Windows Registry key.

    Args:
      parser_mediator (ParserMediator): mediates interactions between parsers
          and other components, such as storage and dfvfs.
      registry_key (dfwinreg.WinRegistryKey): Windows Registry key.
    """
    network_info = {}
    signatures = registry_key.GetSubkeyByName('Signatures')
    if signatures:
      network_info = self._GetNetworkInfo(signatures)

    profiles = registry_key.GetSubkeyByName('Profiles')
    if not profiles:
      return

    for subkey in profiles.GetSubkeys():
      default_gateway_mac, dns_suffix = network_info.get(
          subkey.name, (None, None))

      event_data = WindowsRegistryNetworkEventData()
      event_data.default_gateway_mac = default_gateway_mac
      event_data.dns_suffix = dns_suffix

      ssid_value = subkey.GetValueByName('ProfileName')
      if ssid_value:
        event_data.ssid = ssid_value.GetDataAsObject()

      description_value = subkey.GetValueByName('Description')
      if description_value:
        event_data.description = description_value.GetDataAsObject()

      connection_type_value = subkey.GetValueByName('NameType')
      if connection_type_value:
        connection_type = connection_type_value.GetDataAsObject()
        # TODO: move to formatter.
        connection_type = self._CONNECTION_TYPE.get(
            connection_type, 'unknown')
        event_data.connection_type = connection_type

      date_created_value = subkey.GetValueByName('DateCreated')
      if date_created_value:
        try:
          systemtime_struct = self._SYSTEMTIME_STRUCT.parse(
              date_created_value.data)
        except construct.ConstructError as exception:
          systemtime_struct = None
          parser_mediator.ProduceExtractionError(
              'unable to parse date created with error: {0!s}'.format(
                  exception))

        system_time_tuple = self._EMPTY_SYSTEM_TIME_TUPLE
        if systemtime_struct:
          system_time_tuple = (
              systemtime_struct.year, systemtime_struct.month,
              systemtime_struct.day_of_week, systemtime_struct.day_of_month,
              systemtime_struct.hours, systemtime_struct.minutes,
              systemtime_struct.seconds, systemtime_struct.milliseconds)

        date_time = None
        if system_time_tuple != self._EMPTY_SYSTEM_TIME_TUPLE:
          try:
            date_time = dfdatetime_systemtime.Systemtime(
                system_time_tuple=system_time_tuple)
          except ValueError:
            parser_mediator.ProduceExtractionError(
                'invalid system time: {0!s}'.format(system_time_tuple))

        if date_time:
          event = time_events.DateTimeValuesEvent(
              date_time, definitions.TIME_DESCRIPTION_CREATION)
          parser_mediator.ProduceEventWithEventData(event, event_data)

      date_last_connected_value = subkey.GetValueByName('DateLastConnected')
      if date_last_connected_value:
        try:
          systemtime_struct = self._SYSTEMTIME_STRUCT.parse(
              date_last_connected_value.data)
        except construct.ConstructError as exception:
          systemtime_struct = None
          parser_mediator.ProduceExtractionError(
              'unable to parse date last connected with error: {0!s}'.format(
                  exception))

        system_time_tuple = self._EMPTY_SYSTEM_TIME_TUPLE
        if systemtime_struct:
          system_time_tuple = (
              systemtime_struct.year, systemtime_struct.month,
              systemtime_struct.day_of_week, systemtime_struct.day_of_month,
              systemtime_struct.hours, systemtime_struct.minutes,
              systemtime_struct.seconds, systemtime_struct.milliseconds)

        date_time = None
        if system_time_tuple != self._EMPTY_SYSTEM_TIME_TUPLE:
          try:
            date_time = dfdatetime_systemtime.Systemtime(
                system_time_tuple=system_time_tuple)
          except ValueError:
            parser_mediator.ProduceExtractionError(
                'invalid system time: {0!s}'.format(system_time_tuple))

        if date_time:
          event = time_events.DateTimeValuesEvent(
              date_time, definitions.TIME_DESCRIPTION_LAST_CONNECTED)
          parser_mediator.ProduceEventWithEventData(event, event_data)


winreg.WinRegistryParser.RegisterPlugin(NetworksPlugin)
