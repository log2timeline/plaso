# -*- coding: utf-8 -*-
"""The Android mmssms.db database event formatter."""

from __future__ import unicode_literals

from plaso.formatters import interface
from plaso.formatters import manager


class AndroidSmsFormatter(interface.ConditionalEventFormatter):
  """Formatter for an Android SMS event."""

  DATA_TYPE = 'android:messaging:sms'

  FORMAT_STRING_PIECES = [
      'Type: {sms_type}',
      'Address: {address}',
      'Status: {sms_read}',
      'Message: {body}']

  FORMAT_STRING_SHORT_PIECES = ['{body}']

  SOURCE_LONG = 'Android SMS messages'
  SOURCE_SHORT = 'SMS'


manager.FormattersManager.RegisterFormatter(AndroidSmsFormatter)
