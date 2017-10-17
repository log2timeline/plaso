# -*- coding: utf-8 -*-
"""The UserAssist Windows Registry event formatter."""

from __future__ import unicode_literals

from plaso.formatters import interface
from plaso.formatters import manager


class UserAssistWindowsRegistryEventFormatter(
    interface.ConditionalEventFormatter):
  """Formatter for an UserAssist Windows Registry event."""

  DATA_TYPE = 'windows:registry:userassist'

  FORMAT_STRING_PIECES = [
      '[{key_path}]',
      'UserAssist entry: {entry_index}',
      'Value name: {value_name}',
      'Count: {number_of_executions}',
      'Application focus count: {application_focus_count}',
      'Application focus duration: {application_focus_duration}']

  FORMAT_STRING_SHORT_PIECES = [
      '{value_name}',
      'Count: {number_of_executions}']

  SOURCE_LONG = 'Registry Key: UserAssist'
  SOURCE_SHORT = 'REG'


manager.FormattersManager.RegisterFormatter(
    UserAssistWindowsRegistryEventFormatter)
