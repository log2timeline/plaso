# -*- coding: utf-8 -*-
"""The googlehangouts messages database event formatter."""

from __future__ import unicode_literals

from plaso.formatters import interface
from plaso.formatters import manager


class GoogleMSGFormatter(interface.ConditionalEventFormatter):
  """Formatter for an Google MSG event."""

  DATA_TYPE = 'android:messaging:googlehangouts'

  FORMAT_STRING_PIECES = [
      'Sender: {sender}',
      'Body: {body}',
      'Status: {read}',
      'Type: {msgtype}']

  FORMAT_STRING_SHORT_PIECES = ['{body}']

  SOURCE_LONG = 'Google Hangouts Message'
  SOURCE_SHORT = 'GHM'


manager.FormattersManager.RegisterFormatter(GoogleMSGFormatter)
