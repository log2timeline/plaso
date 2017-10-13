# -*- coding: utf-8 -*-
"""The XChat scrollback file event formatter."""

from __future__ import unicode_literals

from plaso.formatters import interface
from plaso.formatters import manager


class XChatScrollbackFormatter(interface.ConditionalEventFormatter):
  """Formatter for a XChat scrollback file entry event."""

  DATA_TYPE = 'xchat:scrollback:line'

  FORMAT_STRING_SEPARATOR = ''

  FORMAT_STRING_PIECES = [
      '[',
      'nickname: {nickname}',
      ']',
      ' {text}']

  SOURCE_LONG = 'XChat Scrollback File'
  SOURCE_SHORT = 'LOG'


manager.FormattersManager.RegisterFormatter(XChatScrollbackFormatter)
