# -*- coding: utf-8 -*-
"""The Microsoft Office MRU Windows Registry event formatter."""

from __future__ import unicode_literals

from plaso.formatters import interface
from plaso.formatters import manager


class OfficeMRUWindowsRegistryEventFormatter(
    interface.ConditionalEventFormatter):
  """Formatter for a Microsoft Office MRU Windows Registry event."""

  DATA_TYPE = 'windows:registry:office_mru'

  FORMAT_STRING_PIECES = [
      '[{key_path}]',
      'Value: {value_string}']

  FORMAT_STRING_SHORT_PIECES = [
      '{value_string}']

  SOURCE_LONG = 'Registry Key: Microsoft Office MRU'
  SOURCE_SHORT = 'REG'


manager.FormattersManager.RegisterFormatter(
    OfficeMRUWindowsRegistryEventFormatter)
