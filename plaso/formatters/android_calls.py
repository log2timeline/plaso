# -*- coding: utf-8 -*-
"""The Android contacts2.db database event formatter."""

from __future__ import unicode_literals

from plaso.formatters import interface
from plaso.formatters import manager


class AndroidCallFormatter(interface.ConditionalEventFormatter):
  """Formatter for an Android call history event."""

  DATA_TYPE = 'android:event:call'

  FORMAT_STRING_PIECES = [
      '{call_type}',
      'Number: {number}',
      'Name: {name}',
      'Duration: {duration} seconds']

  FORMAT_STRING_SHORT_PIECES = ['{call_type} Call']

  SOURCE_LONG = 'Android Call History'
  SOURCE_SHORT = 'LOG'


manager.FormattersManager.RegisterFormatter(AndroidCallFormatter)
