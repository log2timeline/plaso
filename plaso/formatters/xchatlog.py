# -*- coding: utf-8 -*-
"""The XChat log file event formatter."""

from __future__ import unicode_literals

from plaso.formatters import interface
from plaso.formatters import manager


class XChatLogFormatter(interface.ConditionalEventFormatter):
  """Formatter for a XChat log file entry event."""

  DATA_TYPE = 'xchat:log:line'

  FORMAT_STRING_PIECES = [
      '[nickname: {nickname}]',
      '{text}']

  SOURCE_LONG = 'XChat Log File'
  SOURCE_SHORT = 'LOG'


manager.FormattersManager.RegisterFormatter(XChatLogFormatter)
