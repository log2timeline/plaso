# -*- coding: utf-8 -*-
"""The Mac Notes zhtmlstring event formatter."""
from __future__ import unicode_literals

from plaso.formatters import interface
from plaso.formatters import manager


class MacNotesNotesFormatter(interface.ConditionalEventFormatter):
  """Formatter for a Mac Notes zhtmlstring record."""

  DATA_TYPE = 'mac:notes:zhtmlstring'

  FORMAT_STRING_PIECES = [
      'title: {title}',
      'note_body: {note_text}']

  FORMAT_STRING_SHORT_PIECES = ['title: {title}']

  SOURCE_LONG = 'Mac Notes Zhtmlstring'
  SOURCE_SHORT = 'Mac Notes'


manager.FormattersManager.RegisterFormatter(MacNotesNotesFormatter)
