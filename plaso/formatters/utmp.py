# -*- coding: utf-8 -*-
"""The UTMP binary file event formatter."""

from __future__ import unicode_literals

from plaso.formatters import interface
from plaso.formatters import manager


class UtmpSessionFormatter(interface.ConditionalEventFormatter):
  """Formatter for an UTMP session event."""

  DATA_TYPE = 'linux:utmp:event'

  FORMAT_STRING_PIECES = [
      'User: {username}',
      'Hostname: {hostname}',
      'Terminal: {terminal}',
      'PID: {pid}',
      'Terminal identifier: {terminal_identifier}',
      'Status: {status}',
      'IP Address: {ip_address}',
      'Exit status: {exit_status}']

  FORMAT_STRING_SHORT_PIECES = [
      'User: {username}',
      'PID: {pid}',
      'Status: {status}']

  SOURCE_LONG = 'UTMP session'
  SOURCE_SHORT = 'LOG'

  _STATUS_TYPES = {
      0: 'EMPTY',
      1: 'RUN_LVL',
      2: 'BOOT_TIME',
      3: 'NEW_TIME',
      4: 'OLD_TIME',
      5: 'INIT_PROCESS',
      6: 'LOGIN_PROCESS',
      7: 'USER_PROCESS',
      8: 'DEAD_PROCESS',
      9: 'ACCOUNTING'}

  def __init__(self):
    """Initializes an UTMP session event format helper."""
    super(UtmpSessionFormatter, self).__init__()
    helper = interface.EnumerationEventFormatterHelper(
        default='UNKNOWN', input_attribute='type',
        output_attribute='status', values=self._STATUS_TYPES)

    self.helpers.append(helper)


manager.FormattersManager.RegisterFormatter(UtmpSessionFormatter)
