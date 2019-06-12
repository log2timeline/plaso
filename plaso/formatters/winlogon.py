# -*- coding: utf-8 -*-
"""The Winlogon key event formatter."""

from __future__ import unicode_literals

from plaso.formatters import interface
from plaso.formatters import manager


class WinlogonEventFormatter(interface.ConditionalEventFormatter):
  """Formatter for a Winlogon event."""

  DATA_TYPE = 'windows:registry:winlogon'

  FORMAT_STRING_PIECES = [
      '[{key_path}]',
      'Application: {application}',
      'Command: {command}',
      'Handler: {handler}',
      'Trigger: {trigger}']

  FORMAT_STRING_SHORT_PIECES = [
      '[{key_path}]',
      'Application: {application}',
      'Command: {command}',
      'Handler: {handler}',
      'Trigger: {trigger}']

  SOURCE_LONG = 'Registry Key : Winlogon'
  SOURCE_SHORT = 'REG'


manager.FormattersManager.RegisterFormatter(WinlogonEventFormatter)
