# -*- coding: utf-8 -*-
"""This file contains a xchatlog formatter in plaso."""

from plaso.formatters import interface
from plaso.formatters import manager


class XChatLogFormatter(interface.ConditionalEventFormatter):
  """Formatter for XChat log files."""

  DATA_TYPE = 'xchat:log:line'

  FORMAT_STRING_PIECES = [
      u'[nickname: {nickname}]',
      u'{text}']

  SOURCE_LONG = 'XChat Log File'
  SOURCE_SHORT = 'LOG'


manager.FormattersManager.RegisterFormatter(XChatLogFormatter)
