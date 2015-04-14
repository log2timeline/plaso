# -*- coding: utf-8 -*-
"""The XChat scrollback file event formatter."""

from plaso.formatters import interface
from plaso.formatters import manager


class XChatScrollbackFormatter(interface.ConditionalEventFormatter):
  """Formatter for a XChat scrollback file entry event."""

  DATA_TYPE = 'xchat:scrollback:line'

  FORMAT_STRING_SEPARATOR = u''

  FORMAT_STRING_PIECES = [
      u'[',
      u'nickname: {nickname}',
      u']',
      u' {text}']

  SOURCE_LONG = 'XChat Scrollback File'
  SOURCE_SHORT = 'LOG'


manager.FormattersManager.RegisterFormatter(XChatScrollbackFormatter)
