# -*- coding: utf-8 -*-
"""The UTMPX binary file event formatter."""

from __future__ import unicode_literals

from plaso.formatters import interface
from plaso.formatters import manager


class UtmpxSessionFormatter(interface.ConditionalEventFormatter):
  """Formatter for an UTMPX session event."""

  DATA_TYPE = 'mac:utmpx:event'

  FORMAT_STRING_PIECES = [
      'User: {username}',
      'Status: {status}',
      'Hostname: {hostname}',
      'Terminal: {terminal}',
      'PID: {pid}',
      'Terminal identifier: {terminal_identifier}']

  FORMAT_STRING_SHORT_PIECES = [
      'User: {username}',
      'PID: {pid}',
      'Status: {status}']

  SOURCE_LONG = 'UTMPX session'
  SOURCE_SHORT = 'LOG'

  # 9, 10 and 11 are only for Darwin and IOS.
  _STATUS_TYPES = {
      0: 'EMPTY',
      1: 'RUN_LVL',
      2: 'BOOT_TIME',
      3: 'OLD_TIME',
      4: 'NEW_TIME',
      5: 'INIT_PROCESS',
      6: 'LOGIN_PROCESS',
      7: 'USER_PROCESS',
      8: 'DEAD_PROCESS',
      9: 'ACCOUNTING',
      10: 'SIGNATURE',
      11: 'SHUTDOWN_TIME'}

  def __init__(self):
    """Initializes an UTMPX session event format helper."""
    super(UtmpxSessionFormatter, self).__init__()
    helper = interface.EnumerationEventFormatterHelper(
        default='UNKNOWN', input_attribute='type',
        output_attribute='status', values=self._STATUS_TYPES)

    self.helpers.append(helper)


manager.FormattersManager.RegisterFormatter(UtmpxSessionFormatter)
