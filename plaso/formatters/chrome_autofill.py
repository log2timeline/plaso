# -*- coding: utf-8 -*-
"""The Google Chrome autofill database event formatter."""

from __future__ import unicode_literals

from plaso.formatters import interface
from plaso.formatters import manager


class ChromeAutofillFormatter(interface.ConditionalEventFormatter):
  """Formatter for a Chrome autofill event."""

  DATA_TYPE = 'chrome:autofill:entry'

  FORMAT_STRING_PIECES = [
      'Form field name: {field_name}',
      'Entered value: {value}',
      'Times used: {usage_count}']

  FORMAT_STRING_SHORT_PIECES = [
      '{field_name}:',
      '{value}',
      '({usage_count})']

  SOURCE_LONG = 'Chrome Autofill'
  SOURCE_SHORT = 'WEBHIST'


manager.FormattersManager.RegisterFormatter(ChromeAutofillFormatter)
