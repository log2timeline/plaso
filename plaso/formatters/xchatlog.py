# -*- coding: utf-8 -*-
"""The XChat log file event formatter."""

from plaso.formatters import interface
from plaso.formatters import manager


class XChatLogFormatter(interface.ConditionalEventFormatter):
  """Formatter for a XChat log file entry event."""

  DATA_TYPE = 'xchat:log:line'

  FORMAT_STRING_PIECES = [
      u'[nickname: {nickname}]',
      u'{text}']

  SOURCE_LONG = 'XChat Log File'
  SOURCE_SHORT = 'LOG'


manager.FormattersManager.RegisterFormatter(XChatLogFormatter)
