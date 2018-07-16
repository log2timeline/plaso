# -*- coding: utf-8 -*-
"""The mifit  database event formatter."""

from __future__ import unicode_literals

from plaso.formatters import interface
from plaso.formatters import manager


class MiFitFormatter(interface.ConditionalEventFormatter):
  """Formatter for an mifit."""

  DATA_TYPE = 'iot:mifit'

  FORMAT_STRING_PIECES = [
      'Summary: {summary}',
      'Data: {data}',
      'TimeZone: {timeZone}',
      'Device ID: {deviceID}']

  FORMAT_STRING_SHORT_PIECES = ['{data}']

  SOURCE_LONG = 'MiFitEvent'
  SOURCE_SHORT = 'MiFitEvent'


manager.FormattersManager.RegisterFormatter(MiFitFormatter)
