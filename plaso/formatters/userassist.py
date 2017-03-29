# -*- coding: utf-8 -*-
"""The UserAssist Windows Registry event formatter."""

from plaso.formatters import interface
from plaso.formatters import manager


class UserAssistWindowsRegistryEventFormatter(
    interface.ConditionalEventFormatter):
  """Formatter for an UserAssist Windows Registry event."""

  DATA_TYPE = u'windows:registry:userassist'

  FORMAT_STRING_PIECES = [
      u'[{key_path}]',
      u'UserAssist entry: {entry_index}',
      u'Value name: {value_name}',
      u'Count: {number_of_executions}',
      u'Application focus count: {application_focus_count}',
      u'Application focus duration: {application_focus_duration}']

  FORMAT_STRING_SHORT_PIECES = [
      u'{value_name}',
      u'Count: {number_of_executions}']

  SOURCE_LONG = u'Registry Key: UserAssist'
  SOURCE_SHORT = u'REG'


manager.FormattersManager.RegisterFormatter(
    UserAssistWindowsRegistryEventFormatter)
