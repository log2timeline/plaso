# -*- coding: utf-8 -*-
"""The Microsoft Office MRU Windows Registry event formatter."""

from plaso.formatters import interface
from plaso.formatters import manager


class OfficeMRUWindowsRegistryEventFormatter(
    interface.ConditionalEventFormatter):
  """Formatter for a Microsoft Office MRU Windows Registry event."""

  DATA_TYPE = u'windows:registry:office_mru'

  FORMAT_STRING_PIECES = [
      u'[{key_path}]',
      u'Value: {value_string}']

  FORMAT_STRING_SHORT_PIECES = [
      u'{value_string}']

  SOURCE_LONG = u'Registry Key: Microsoft Office MRU'
  SOURCE_SHORT = u'REG'


manager.FormattersManager.RegisterFormatter(
    OfficeMRUWindowsRegistryEventFormatter)
