# -*- coding: utf-8 -*-
"""Formatter for Android mmssms.db database events."""

from plaso.formatters import interface
from plaso.formatters import manager


class AndroidSmsFormatter(interface.ConditionalEventFormatter):
  """Formatter for Android sms events."""

  DATA_TYPE = 'android:messaging:sms'

  FORMAT_STRING_PIECES = [
      u'Type: {sms_type}',
      u'Address: {address}',
      u'Status: {sms_read}',
      u'Message: {body}']

  FORMAT_STRING_SHORT_PIECES = [u'{body}']

  SOURCE_LONG = 'Android SMS messages'
  SOURCE_SHORT = 'SMS'


manager.FormattersManager.RegisterFormatter(AndroidSmsFormatter)
