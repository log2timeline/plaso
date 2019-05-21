# -*- coding: utf-8 -*-
"""The Google Chrome extension activity database event formatter."""

from __future__ import unicode_literals

from plaso.formatters import interface
from plaso.formatters import manager
from plaso.lib import errors


class ChromeExtensionActivityEventFormatter(
    interface.ConditionalEventFormatter):
  """Formatter for a Chrome extension activity event."""

  DATA_TYPE = 'chrome:extension_activity:activity_log'

  FORMAT_STRING_PIECES = [
      'Chrome extension: {extension_id}',
      'Action type: {action_type}',
      'Activity identifier: {activity_id}',
      'Page URL: {page_url}',
      'Page title: {page_title}',
      'API name: {api_name}',
      'Args: {args}',
      'Other: {other}']

  FORMAT_STRING_SHORT_PIECES = [
      '{extension_id}',
      '{api_name}',
      '{args}']

  SOURCE_LONG = 'Chrome Extension Activity'
  SOURCE_SHORT = 'WEBHIST'

  # From:
  # https://chromium.googlesource.com/chromium/src.git/+/master/chrome/browser/extensions/activity_log/activity_actions.h
  _CHROME_ACTION_TYPES = {
      0 : 'API call',
      1 : 'API event callback',
      2 : 'API action blocked',
      3 : 'Content Script inserted',
      4 : 'DOM access',
      5 : 'DOM event',
      6 : 'WebRequest',
      1001 : 'Unspecified'
  }

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

    action_type = event_values.get('action_type')
    event_values['action_type'] = '%s (type %d)'%(
        self._CHROME_ACTION_TYPES.get(action_type, 'unknown action_type'),
        action_type
    )

    return self._ConditionalFormatMessages(event_values)


manager.FormattersManager.RegisterFormatter(
    ChromeExtensionActivityEventFormatter)
