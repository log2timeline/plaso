# -*- coding: utf-8 -*-
"""The Java WebStart Cache IDX event formatter."""

from plaso.formatters import interface
from plaso.formatters import manager


class JavaIDXFormatter(interface.ConditionalEventFormatter):
  """Formatter for an Java WebStart Cache IDX download event."""

  DATA_TYPE = 'java:download:idx'

  FORMAT_STRING_PIECES = [
      u'IDX Version: {idx_version}',
      u'Host IP address: ({ip_address})',
      u'Download URL: {url}']

  SOURCE_LONG = 'Java Cache IDX'
  SOURCE_SHORT = 'JAVA_IDX'


manager.FormattersManager.RegisterFormatter(JavaIDXFormatter)
