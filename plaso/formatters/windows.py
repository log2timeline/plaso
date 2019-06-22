# -*- coding: utf-8 -*-
"""The Windows event formatter."""

from __future__ import unicode_literals

from plaso.formatters import interface
from plaso.formatters import manager


class WindowsDistributedLinkTrackingCreationEventFormatter(
    interface.ConditionalEventFormatter):
  """Formatter for a Windows distributed link creation event."""

  DATA_TYPE = 'windows:distributed_link_tracking:creation'

  FORMAT_STRING_PIECES = [
      '{uuid}',
      'MAC address: {mac_address}',
      'Origin: {origin}']

  FORMAT_STRING_SHORT_PIECES = [
      '{uuid}',
      'Origin: {origin}']

  SOURCE_LONG = 'System'
  SOURCE_SHORT = 'LOG'


class WindowsRegistryNetworkEventFormatter(interface.ConditionalEventFormatter):
  """Formatter for a Windows NetworkList event formatter."""

  DATA_TYPE = 'windows:registry:network'

  FORMAT_STRING_PIECES = [
      'SSID: {ssid}',
      'Description: {description}',
      'Connection Type: {connection_type}',
      'Default Gateway Mac: {default_gateway_mac}',
      'DNS Suffix: {dns_suffix}']

  SOURCE_LONG = 'System: Network Connection'
  SOURCE_SHORT = 'LOG'


class WindowsVolumeCreationEventFormatter(interface.ConditionalEventFormatter):
  """Formatter for a Windows volume creation event."""

  DATA_TYPE = 'windows:volume:creation'

  FORMAT_STRING_PIECES = [
      '{device_path}',
      'Serial number: 0x{serial_number:08X}',
      'Origin: {origin}']

  FORMAT_STRING_SHORT_PIECES = [
      '{device_path}',
      'Origin: {origin}']

  SOURCE_LONG = 'System'
  SOURCE_SHORT = 'LOG'


manager.FormattersManager.RegisterFormatters([
    WindowsDistributedLinkTrackingCreationEventFormatter,
    WindowsRegistryNetworkEventFormatter,
    WindowsVolumeCreationEventFormatter])
