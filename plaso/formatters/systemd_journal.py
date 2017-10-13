# -*- coding: utf-8 -*-
"""The Systemd journal file event formatter."""

from __future__ import unicode_literals

from plaso.formatters import interface
from plaso.formatters import manager


class SystemdJournalEventFormatter(interface.ConditionalEventFormatter):
  """Formatter for a Systemd journal event."""

  DATA_TYPE = 'systemd:journal'

  # It would be nice to have the _MACHINE_ID field, which is a unique identifier
  # for the system, and hopefully more unique than the _HOSTNAME field.
  # Unfortunately, journal files that have not been closed cleanly may contain
  # entries that have no _MACHINE_ID field.

  FORMAT_STRING_SEPARATOR = ''

  FORMAT_STRING_PIECES = [
      '{hostname} ',
      '[',
      '{reporter}',
      ', pid: {pid}',
      '] {body}']

  SOURCE_LONG = 'systemd-journal'
  SOURCE_SHORT = 'LOG'


manager.FormattersManager.RegisterFormatter(SystemdJournalEventFormatter)
