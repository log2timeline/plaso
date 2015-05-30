# -*- coding: utf-8 -*-
"""The selinux event formatter."""

from plaso.formatters import interface
from plaso.formatters import manager


class SELinuxFormatter(interface.ConditionalEventFormatter):
  """Formatter for a selinux log file event."""

  DATA_TYPE = u'selinux:line'

  FORMAT_STRING_SEPARATOR = u''

  FORMAT_STRING_PIECES = [
      u'[',
      u'audit_type: {audit_type}',
      u', pid: {pid}',
      u']',
      u' {body}']

  SOURCE_LONG = u'Audit log File'
  SOURCE_SHORT = u'LOG'


manager.FormattersManager.RegisterFormatter(SELinuxFormatter)
