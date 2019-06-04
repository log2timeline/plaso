# -*- coding: utf-8 -*-
"""The Explorer ProgramsCache event formatter."""

from __future__ import unicode_literals

from plaso.formatters import interface
from plaso.formatters import manager


class ExplorerProgramsCacheEventFormatter(interface.ConditionalEventFormatter):
  """Formatter for an Explorer ProgramsCache event."""

  DATA_TYPE = 'windows:registry:explorer:programcache'

  FORMAT_STRING_PIECES = [
      'Key: {key_path}',
      'Value: {value_name}',
      'Entries: [{entries}]']

  SOURCE_LONG = 'Registry Key'
  SOURCE_SHORT = 'REG'


manager.FormattersManager.RegisterFormatter(ExplorerProgramsCacheEventFormatter)
