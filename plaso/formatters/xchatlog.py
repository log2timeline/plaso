# -*- coding: utf-8 -*-
"""The XChat log file event formatter."""

from plaso.formatters import interface
from plaso.formatters import manager


class XChatLogFormatter(interface.ConditionalEventFormatter):
  """Formatter for a XChat log file entry event."""

  DATA_TYPE = u'xchat:log:line'

  FORMAT_STRING_PIECES = [
      u'[nickname: {nickname}]',
      u'{text}']

  SOURCE_LONG = u'XChat Log File'
  SOURCE_SHORT = u'LOG'


manager.FormattersManager.RegisterFormatter(XChatLogFormatter)
