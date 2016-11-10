# -*- coding: utf-8 -*-
"""The Google Chrome Preferences file event formatter."""

from plaso.formatters import interface
from plaso.formatters import manager


class ChromePreferencesClearHistoryEventFormatter(
    interface.ConditionalEventFormatter):
  """Formatter for Chrome history clearing events."""

  DATA_TYPE = u'chrome:preferences:clear_history'

  FORMAT_STRING_PIECES = [u'{message}']

  FORMAT_STRING_SHORT_PIECES = [u'{message}']

  SOURCE_LONG = u'Chrome History Deletion'
  SOURCE_SHORT = u'LOG'


class ChromeExtensionInstallationEventFormatter(
    interface.ConditionalEventFormatter):
  """Formatter for a Chrome extension installation event."""

  DATA_TYPE = u'chrome:preferences:extension_installation'

  FORMAT_STRING_PIECES = [
      u'CRX ID: {extension_id}',
      u'CRX Name: {extension_name}',
      u'Path: {path}']

  FORMAT_STRING_SHORT_PIECES = [
      u'{extension_id}',
      u'{path}']

  SOURCE_LONG = u'Chrome Extension Installation'
  SOURCE_SHORT = u'LOG'


manager.FormattersManager.RegisterFormatters([
    ChromeExtensionInstallationEventFormatter,
    ChromePreferencesClearHistoryEventFormatter
])
