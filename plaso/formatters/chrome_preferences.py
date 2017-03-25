# -*- coding: utf-8 -*-
"""The Google Chrome Preferences file event formatter."""

from plaso.formatters import interface
from plaso.formatters import manager
from plaso.lib import errors


class ChromePreferencesClearHistoryEventFormatter(
    interface.ConditionalEventFormatter):
  """Formatter for Chrome history clearing events."""

  DATA_TYPE = u'chrome:preferences:clear_history'

  FORMAT_STRING_PIECES = [u'{message}']

  FORMAT_STRING_SHORT_PIECES = [u'{message}']

  SOURCE_LONG = u'Chrome History Deletion'
  SOURCE_SHORT = u'LOG'


class ChromeExtensionsAutoupdaterEvent(interface.ConditionalEventFormatter):
  """Formatter for Chrome Extensions Autoupdater events."""

  DATA_TYPE = u'chrome:preferences:extensions_autoupdater'

  FORMAT_STRING_PIECES = [u'{message}']

  FORMAT_STRING_SHORT_PIECES = [u'{message}']

  SOURCE_LONG = u'Chrome Extensions Autoupdater'
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


class ChromeContentSettingsExceptionsFormatter(
    interface.ConditionalEventFormatter):
  """Formatter for a Chrome content_settings exceptions event."""

  DATA_TYPE = u'chrome:preferences:content_settings:exceptions'

  FORMAT_STRING_PIECES = [
      u'Permission {permission}',
      u'used by {subject}']

  FORMAT_STRING_SHORT_PIECES = [
      u'Permission {permission}',
      u'used by {subject}']

  SOURCE_LONG = u'Chrome Permission Event'
  SOURCE_SHORT = u'LOG'

  def GetMessages(self, unused_formatter_mediator, event):
    """Determines the formatted message strings for an event object.

    Args:
      formatter_mediator (FormatterMediator): mediates the interactions between
          formatters and other components, such as storage and Windows EventLog
          resources.
      event (EventObject): event.

    Returns:
      tuple(str, str): formatted message string and short message string.

    Raises:
      WrongFormatter: if the event object cannot be formatted by the formatter.
    """
    if self.DATA_TYPE != event.data_type:
      raise errors.WrongFormatter(u'Unsupported data type: {0:s}.'.format(
          event.data_type))

    event_values = event.CopyToDict()

    primary_url = event_values[u'primary_url']
    secondary_url = event_values[u'secondary_url']

    # There is apparently a bug, either in GURL.cc or
    # content_settings_pattern.cc where URLs with file:// scheme are stored in
    # the URL as an empty string, which is later detected as being Invalid, and
    # Chrome produces the following example logs:
    # content_settings_pref.cc(469)] Invalid pattern strings: https://a.com:443,
    # content_settings_pref.cc(295)] Invalid pattern strings: ,
    # content_settings_pref.cc(295)] Invalid pattern strings: ,*
    # More research needed, could be related to https://crbug.com/132659

    if primary_url == u'':
      subject = u'local file'

    elif primary_url == secondary_url or secondary_url == u'*':
      subject = primary_url

    elif secondary_url == u'':
      subject = u'{0:s} embedded in local file'.format(primary_url)

    else:
      subject = u'{0:s} embedded in {1:s}'.format(primary_url, secondary_url)

    event_values[u'subject'] = subject

    return self._ConditionalFormatMessages(event_values)


manager.FormattersManager.RegisterFormatters([
    ChromeContentSettingsExceptionsFormatter,
    ChromeExtensionsAutoupdaterEvent,
    ChromeExtensionInstallationEventFormatter,
    ChromePreferencesClearHistoryEventFormatter])
