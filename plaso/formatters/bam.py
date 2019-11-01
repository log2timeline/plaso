# -*- coding: utf-8 -*-
"""The Windows Registry Background Activity Moderator event formatter."""

from __future__ import unicode_literals

from plaso.formatters import interface
from plaso.formatters import manager


class BackgroundActivityModeratorFormatter(interface.ConditionalEventFormatter):
  """Formatter for a Background Activity Moderator Windows Registry event."""

  DATA_TYPE = 'windows:registry:bam'

  FORMAT_STRING_PIECES = [
      '{binary_path}',
      '[{user_sid}]']

  FORMAT_STRING_SHORT_PIECES = ['{binary_path}']

  SOURCE_LONG = 'Background Activity Moderator Registry Entry'
  SOURCE_SHORT = 'REG'


manager.FormattersManager.RegisterFormatter(
    BackgroundActivityModeratorFormatter)
