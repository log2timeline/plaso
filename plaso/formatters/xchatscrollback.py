# -*- coding: utf-8 -*-
"""This file contains a xchatscrollback formatter in plaso."""

from plaso.formatters import interface
from plaso.formatters import manager


class XChatScrollbackFormatter(interface.ConditionalEventFormatter):
  """Formatter for XChat scrollback files."""

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
