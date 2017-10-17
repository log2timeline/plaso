# -*- coding: utf-8 -*-
"""The McAfee AV Logs file event formatter."""

from __future__ import unicode_literals

from plaso.formatters import interface
from plaso.formatters import manager


class McafeeAccessProtectionLogEventFormatter(
    interface.ConditionalEventFormatter):
  """Formatter for a McAfee Access Protection Log event."""

  DATA_TYPE = 'av:mcafee:accessprotectionlog'

  FORMAT_STRING_PIECES = [
      'File Name: {filename}',
      'User: {username}',
      '{trigger_location}',
      '{status}',
      '{rule}',
      '{action}']

  FORMAT_STRING_SHORT_PIECES = [
      '{filename}',
      '{action}']

  SOURCE_LONG = 'McAfee Access Protection Log'
  SOURCE_SHORT = 'LOG'


manager.FormattersManager.RegisterFormatter(
    McafeeAccessProtectionLogEventFormatter)
