# -*- coding: utf-8 -*-
"""The USBStor event formatter."""

from __future__ import unicode_literals

from plaso.formatters import interface
from plaso.formatters import manager


class USBStorEventFormatter(interface.ConditionalEventFormatter):
  """Formatter for a USBStor event."""

  DATA_TYPE = 'windows:registry:usbstor'

  FORMAT_STRING_PIECES = [
      '[{key_path}]',
      'Device type: {device_type}',
      'Display name: {display_name}',
      'Product: {product}',
      'Revision: {revision}',
      'Serial: {serial}',
      'Subkey name: {subkey_name}',
      'Vendor: {vendor}']

  FORMAT_STRING_SHORT_PIECES = [
      '[{key_path}]',
      'Device type: {device_type}',
      'Display name: {display_name}',
      'Product: {product}',
      'Revision: {revision}',
      'Serial: {serial}',
      'Subkey name: {subkey_name}',
      'Vendor: {vendor}']

  SOURCE_LONG = 'Registry Key : USBStor Entries'
  SOURCE_SHORT = 'REG'


manager.FormattersManager.RegisterFormatter(USBStorEventFormatter)
