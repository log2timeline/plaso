# -*- coding: utf-8 -*-
"""The Android contacts2.db database event formatter."""

from plaso.formatters import interface
from plaso.formatters import manager


class AndroidCallFormatter(interface.ConditionalEventFormatter):
  """Formatter for an Android call history event."""

  DATA_TYPE = u'android:event:call'

  FORMAT_STRING_PIECES = [
      u'{call_type}',
      u'Number: {number}',
      u'Name: {name}',
      u'Duration: {duration} seconds']

  FORMAT_STRING_SHORT_PIECES = [u'{call_type} Call']

  SOURCE_LONG = u'Android Call History'
  SOURCE_SHORT = u'LOG'


manager.FormattersManager.RegisterFormatter(AndroidCallFormatter)
