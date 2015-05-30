# -*- coding: utf-8 -*-
"""The McAfee AV Logs file event formatter."""

from plaso.formatters import interface
from plaso.formatters import manager


class McafeeAccessProtectionLogEventFormatter(
    interface.ConditionalEventFormatter):
  """Formatter for a McAfee Access Protection Log event."""

  DATA_TYPE = u'av:mcafee:accessprotectionlog'

  FORMAT_STRING_PIECES = [
      u'File Name: {filename}',
      u'User: {username}',
      u'{trigger_location}',
      u'{status}',
      u'{rule}',
      u'{action}']

  FORMAT_STRING_SHORT_PIECES = [
      u'{filename}',
      u'{action}']

  SOURCE_LONG = u'McAfee Access Protection Log'
  SOURCE_SHORT = u'LOG'


manager.FormattersManager.RegisterFormatter(
    McafeeAccessProtectionLogEventFormatter)
