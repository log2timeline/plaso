# -*- coding: utf-8 -*-
"""Formatter for the McAfee AV Logs files."""

from plaso.formatters import interface
from plaso.formatters import manager


class McafeeAccessProtectionLogEventFormatter(interface.EventFormatter):
  """Class that formats the McAfee Access Protection Log events."""

  DATA_TYPE = 'av:mcafee:accessprotectionlog'

  # The format string.
  FORMAT_STRING = (u'File Name: {filename} User: {username} {trigger_location} '
                   u'{status} {rule} {action}')
  FORMAT_STRING_SHORT = u'{filename} {action}'

  SOURCE_LONG = 'McAfee Access Protection Log'
  SOURCE_SHORT = 'LOG'


manager.FormattersManager.RegisterFormatter(
    McafeeAccessProtectionLogEventFormatter)
