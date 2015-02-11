# -*- coding: utf-8 -*-
"""Formatter for Java Cache IDX events."""

from plaso.formatters import interface
from plaso.formatters import manager


class JavaIDXFormatter(interface.ConditionalEventFormatter):
  """Formatter for a Java Cache IDX download item."""

  DATA_TYPE = 'java:download:idx'

  SOURCE_LONG = 'Java Cache IDX'
  SOURCE_SHORT = 'JAVA_IDX'

  FORMAT_STRING_PIECES = [
      u'IDX Version: {idx_version}',
      u'Host IP address: ({ip_address})',
      u'Download URL: {url}']


manager.FormattersManager.RegisterFormatter(JavaIDXFormatter)
