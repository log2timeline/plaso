# -*- coding: utf-8 -*-
"""The syslog SSH file event formatter."""

from __future__ import unicode_literals

from plaso.formatters import interface
from plaso.formatters import manager


class SSHLoginEventFormatter(interface.ConditionalEventFormatter):
  """Formatter for a SSH successful login event."""

  DATA_TYPE = 'syslog:ssh:login'

  FORMAT_STRING_SEPARATOR = ''

  FORMAT_STRING_PIECES = [
      'Successful login of user: {username}',
      'from {address}:',
      '{port}',
      'using authentication method: {authentication_method}',
      'ssh pid: {pid}',]

  FORMAT_STRING_SHORT = '{body}'

  SOURCE_LONG = 'SSH log'
  SOURCE_SHORT = 'LOG'


class SSHFailedConnectionEventFormatter(interface.ConditionalEventFormatter):
  """Formatter for a SSH failed connection event."""

  DATA_TYPE = 'syslog:ssh:failed_connection'

  FORMAT_STRING_SEPARATOR = ''

  FORMAT_STRING_PIECES = [
      'Unsuccessful connection of user: {username}',
      'from {address}:',
      '{port}',
      'using authentication method: {authentication_method}',
      'ssh pid: {pid}', ]

  FORMAT_STRING_SHORT = '{body}'

  SOURCE_LONG = 'SSH log'
  SOURCE_SHORT = 'LOG'


class SSHOpenedConnectionEventFormatter(interface.ConditionalEventFormatter):
  """Formatter for a SSH opened connection event."""

  DATA_TYPE = 'syslog:ssh:opened_connection'

  FORMAT_STRING_SEPARATOR = ''

  FORMAT_STRING_PIECES = [
      'Connection opened {address}:',
      '{port}',
      'ssh pid: {pid}',]

  FORMAT_STRING_SHORT = '{body}'

  SOURCE_LONG = 'SSH log'
  SOURCE_SHORT = 'LOG'


manager.FormattersManager.RegisterFormatters([
    SSHLoginEventFormatter, SSHFailedConnectionEventFormatter,
    SSHOpenedConnectionEventFormatter])
