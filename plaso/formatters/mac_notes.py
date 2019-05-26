# -*- coding: utf-8 -*-
"""The Mac Notes event formatter."""
from __future__ import unicode_literals

from plaso.formatters import interface
from plaso.formatters import manager


class MacNotesNotesFormatter(interface.ConditionalEventFormatter):
  """Formatter for a Mac Notes record"""

  DATA_TYPE = 'mac:notes:note'

  FORMAT_STRING_PIECES = [
      'title:{title}',
      'note_text:{text}']

  FORMAT_STRING_SHORT_PIECES = ['title:{title}']

  SOURCE_LONG = 'Mac Notes'
  SOURCE_SHORT = 'Mac Note'


manager.FormattersManager.RegisterFormatter(MacNotesNotesFormatter)
