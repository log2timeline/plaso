# -*- coding: utf-8 -*-
"""The Windows event formatter."""

from plaso.formatters import interface
from plaso.formatters import manager


class WindowsDistributedLinkTrackingCreationEventFormatter(
    interface.ConditionalEventFormatter):
  """Formatter for a Windows distributed link creation event."""

  DATA_TYPE = u'windows:distributed_link_tracking:creation'

  FORMAT_STRING_PIECES = [
      u'{uuid}',
      u'MAC address: {mac_address}',
      u'Origin: {origin}']

  FORMAT_STRING_SHORT_PIECES = [
      u'{uuid}',
      u'Origin: {origin}']

  SOURCE_LONG = u'System'
  SOURCE_SHORT = u'LOG'


class WindowsRegistryInstallationEvent(interface.ConditionalEventFormatter):
  """Formatter for a Windows installation event."""

  DATA_TYPE = u'windows:registry:installation'

  FORMAT_STRING_PIECES = [
      u'{product_name}',
      u'{version}',
      u'{service_pack}',
      u'Owner: owner',
      u'Origin: {key_path}']

  FORMAT_STRING_SHORT_PIECES = [
      u'{product_name}',
      u'{version}',
      u'{service_pack}',
      u'Origin: {key_path}']

  SOURCE_LONG = u'System'
  SOURCE_SHORT = u'LOG'


class WindowsVolumeCreationEventFormatter(interface.ConditionalEventFormatter):
  """Formatter for a Windows volume creation event."""

  DATA_TYPE = u'windows:volume:creation'

  FORMAT_STRING_PIECES = [
      u'{device_path}',
      u'Serial number: 0x{serial_number:08X}',
      u'Origin: {origin}']

  FORMAT_STRING_SHORT_PIECES = [
      u'{device_path}',
      u'Origin: {origin}']

  SOURCE_LONG = u'System'
  SOURCE_SHORT = u'LOG'


manager.FormattersManager.RegisterFormatters([
    WindowsDistributedLinkTrackingCreationEventFormatter,
    WindowsRegistryInstallationEvent,
    WindowsVolumeCreationEventFormatter])
