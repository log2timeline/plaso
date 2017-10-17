# -*- coding: utf-8 -*-
"""The selinux event formatter."""

from __future__ import unicode_literals

from plaso.formatters import interface
from plaso.formatters import manager


class SELinuxFormatter(interface.ConditionalEventFormatter):
  """Formatter for a selinux log file event."""

  DATA_TYPE = 'selinux:line'

  FORMAT_STRING_SEPARATOR = ''

  FORMAT_STRING_PIECES = [
      '[',
      'audit_type: {audit_type}',
      ', pid: {pid}',
      ']',
      ' {body}']

  SOURCE_LONG = 'Audit log File'
  SOURCE_SHORT = 'LOG'


manager.FormattersManager.RegisterFormatter(SELinuxFormatter)
