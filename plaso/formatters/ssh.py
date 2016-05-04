# -*- coding: utf-8 -*-
"""The syslog SSH file event formatter."""

from plaso.formatters import interface
from plaso.formatters import manager


class SSHLoginEventFormatter(interface.ConditionalEventFormatter):
  """Formatter for a SSH successful login event."""

  DATA_TYPE = u'syslog:ssh:login'

  FORMAT_STRING_SEPARATOR = u''

  FORMAT_STRING_PIECES = [
      u'Successful login of user: {username}',
      u'from {address}:',
      u'{port}',
      u'using authentication method: {authentication_method}',
      u'ssh pid: {pid}',]

  FORMAT_STRING_SHORT = u'{body}'

  SOURCE_LONG = u'SSH log'
  SOURCE_SHORT = u'LOG'


class SSHFailedConnectionEventFormatter(interface.ConditionalEventFormatter):
  """Formatter for a SSH failed connection event."""

  DATA_TYPE = u'syslog:ssh:failed_connection'

  FORMAT_STRING_SEPARATOR = u''

  FORMAT_STRING_PIECES = [
      u'Unsuccessful connection of user: {username}',
      u'from {address}:',
      u'{port}',
      u'using authentication method: {authentication_method}',
      u'ssh pid: {pid}', ]

  FORMAT_STRING_SHORT = u'{body}'

  SOURCE_LONG = u'SSH log'
  SOURCE_SHORT = u'LOG'


class SSHOpenedConnectionEventFormatter(interface.ConditionalEventFormatter):
  """Formatter for a SSH opened connection event."""

  DATA_TYPE = u'syslog:ssh:opened_connection'

  FORMAT_STRING_SEPARATOR = u''

  FORMAT_STRING_PIECES = [
      u'Connection opened {address}:',
      u'{port}',
      u'ssh pid: {pid}',]

  FORMAT_STRING_SHORT = u'{body}'

  SOURCE_LONG = u'SSH log'
  SOURCE_SHORT = u'LOG'


manager.FormattersManager.RegisterFormatters([
    SSHLoginEventFormatter, SSHFailedConnectionEventFormatter,
    SSHOpenedConnectionEventFormatter])
