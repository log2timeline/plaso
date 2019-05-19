# -*- coding: utf-8 -*-
"""The Google Chrome Preferences file event formatter."""

from __future__ import unicode_literals

from plaso.formatters import interface
from plaso.formatters import manager
from plaso.lib import errors


class ChromePreferencesClearHistoryEventFormatter(
    interface.ConditionalEventFormatter):
  """Formatter for Chrome history clearing events."""

  DATA_TYPE = 'chrome:preferences:clear_history'

  FORMAT_STRING_PIECES = ['{message}']

  FORMAT_STRING_SHORT_PIECES = ['{message}']

  SOURCE_LONG = 'Chrome History Deletion'
  SOURCE_SHORT = 'LOG'


class ChromeExtensionsAutoupdaterEvent(interface.ConditionalEventFormatter):
  """Formatter for Chrome Extensions Autoupdater events."""

  DATA_TYPE = 'chrome:preferences:extensions_autoupdater'

  FORMAT_STRING_PIECES = ['{message}']

  FORMAT_STRING_SHORT_PIECES = ['{message}']

  SOURCE_LONG = 'Chrome Extensions Autoupdater'
  SOURCE_SHORT = 'LOG'


class ChromeExtensionInstallationEventFormatter(
    interface.ConditionalEventFormatter):
  """Formatter for a Chrome extension installation event."""

  DATA_TYPE = 'chrome:preferences:extension_installation'

  FORMAT_STRING_PIECES = [
      'CRX ID: {extension_id}',
      'CRX Name: {extension_name}',
      'Path: {path}']

  FORMAT_STRING_SHORT_PIECES = [
      '{extension_id}',
      '{path}']

  SOURCE_LONG = 'Chrome Extension Installation'
  SOURCE_SHORT = 'LOG'


class ChromeContentSettingsExceptionsFormatter(
    interface.ConditionalEventFormatter):
  """Formatter for a Chrome content_settings exceptions event."""

  DATA_TYPE = 'chrome:preferences:content_settings:exceptions'

  FORMAT_STRING_PIECES = [
      'Permission {permission}',
      'used by {subject}']

  FORMAT_STRING_SHORT_PIECES = [
      'Permission {permission}',
      'used by {subject}']

  SOURCE_LONG = 'Chrome Permission Event'
  SOURCE_SHORT = 'LOG'

  # pylint: disable=unused-argument
  def GetMessages(self, formatter_mediator, event_data):
    """Determines the formatted message strings for the event data.

    Args:
      formatter_mediator (FormatterMediator): mediates the interactions
          between formatters and other components, such as storage and Windows
          EventLog resources.
      event_data (EventData): event data.

    Returns:
      tuple(str, str): formatted message string and short message string.

    Raises:
      WrongFormatter: if the event data cannot be formatted by the formatter.
    """
    if self.DATA_TYPE != event_data.data_type:
      raise errors.WrongFormatter('Unsupported data type: {0:s}.'.format(
          event_data.data_type))

    event_values = event_data.CopyToDict()

    primary_url = event_values['primary_url']
    secondary_url = event_values['secondary_url']

    # There is apparently a bug, either in GURL.cc or
    # content_settings_pattern.cc where URLs with file:// scheme are stored in
    # the URL as an empty string, which is later detected as being Invalid, and
    # Chrome produces the following example logs:
    # content_settings_pref.cc(469)] Invalid pattern strings: https://a.com:443,
    # content_settings_pref.cc(295)] Invalid pattern strings: ,
    # content_settings_pref.cc(295)] Invalid pattern strings: ,*
    # More research needed, could be related to https://crbug.com/132659

    if primary_url == '':
      subject = 'local file'

    elif secondary_url in (primary_url, '*'):
      subject = primary_url

    elif secondary_url == '':
      subject = '{0:s} embedded in local file'.format(primary_url)

    else:
      subject = '{0:s} embedded in {1:s}'.format(primary_url, secondary_url)

    event_values['subject'] = subject

    return self._ConditionalFormatMessages(event_values)


manager.FormattersManager.RegisterFormatters([
    ChromeContentSettingsExceptionsFormatter,
    ChromeExtensionsAutoupdaterEvent,
    ChromeExtensionInstallationEventFormatter,
    ChromePreferencesClearHistoryEventFormatter])
