# -*- coding: utf-8 -*-
"""The Systemd journam file event formatter."""

from plaso.formatters import interface
from plaso.formatters import manager
from plaso.lib import errors

class SystemdJournalEventFormatter(interface.ConditionalEventFormatter):
  """Formatter for a Systemd journal event."""

  DATA_TYPE = u'systemd:journal:event'

  FORMAT_STRING_SEPARATOR = u''

  SOURCE_LONG = u'systemd-journal'
  SOURCE_SHORT = u'LOG'

  FORMAT_STRING_PIECES = [
      u'[{_HOSTNAME}/{_MACHINE_ID}] ',
      u'{SYSLOG_IDENTIFIER} ',
      u'{MESSAGE}',
  ]


class SystemdJournalUserlandEventFormatter(SystemdJournalEventFormatter):
  """Formatter for a Systemd journal userland event."""

  DATA_TYPE = u'systemd:journal:userland'

  FORMAT_STRING_SEPARATOR = u''

  SOURCE_LONG = u'systemd-journal'
  SOURCE_SHORT = u'LOG'

  FORMAT_STRING_PIECES = [
      u'[{_HOSTNAME}/{_MACHINE_ID} ',
      u'{SYSLOG_IDENTIFIER}[{_PID}]] ',
      u'{MESSAGE}',
  ]



manager.FormattersManager.RegisterFormatters([SystemdJournalEventFormatter,
                                              SystemdJournalUserlandEventFormatter])
