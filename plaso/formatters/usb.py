# -*- coding: utf-8 -*-
"""The Windows USB device event formatter."""

from __future__ import unicode_literals

from plaso.formatters import interface
from plaso.formatters import manager


class WindowsUSBDeviceEventFormatter(interface.ConditionalEventFormatter):
  """Formatter for a Windows USB device event."""

  DATA_TYPE = 'windows:registry:usb'

  FORMAT_STRING_PIECES = [
      '[{key_path}]',
      'Product: {product}',
      'Serial: {serial}',
      'Subkey name: {subkey_name}',
      'Vendor: {vendor}']

  FORMAT_STRING_SHORT_PIECES = [
      '[{key_path}]',
      'Product: {product}',
      'Serial: {serial}',
      'Subkey name: {subkey_name}',
      'Vendor: {vendor}']

  SOURCE_LONG = 'Registry Key : USB Entries'
  SOURCE_SHORT = 'REG'


manager.FormattersManager.RegisterFormatter(WindowsUSBDeviceEventFormatter)
