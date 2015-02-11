# -*- coding: utf-8 -*-
"""Formatter for Android contacts2.db database events."""

from plaso.formatters import interface
from plaso.formatters import manager


class AndroidCallFormatter(interface.ConditionalEventFormatter):
  """Formatter for Android call history events."""

  DATA_TYPE = 'android:event:call'

  FORMAT_STRING_PIECES = [
      u'{call_type}',
      u'Number: {number}',
      u'Name: {name}',
      u'Duration: {duration} seconds']

  FORMAT_STRING_SHORT_PIECES = [u'{call_type} Call']

  SOURCE_LONG = 'Android Call History'
  SOURCE_SHORT = 'LOG'


manager.FormattersManager.RegisterFormatter(AndroidCallFormatter)
