# -*- coding: utf-8 -*-
"""This file contains a formatter for Plist Events."""

from plaso.formatters import interface
from plaso.formatters import manager


class PlistFormatter(interface.ConditionalEventFormatter):
  """Event Formatter for plist keys."""

  DATA_TYPE = 'plist:key'

  FORMAT_STRING_SEPARATOR = u''

  FORMAT_STRING_PIECES = [
      u'{root}/',
      u'{key}',
      u' {desc}']

  SOURCE_LONG = 'Plist Entry'
  SOURCE_SHORT = 'PLIST'


manager.FormattersManager.RegisterFormatter(PlistFormatter)
