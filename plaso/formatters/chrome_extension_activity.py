# -*- coding: utf-8 -*-
"""The Google Chrome extension activity database event formatter."""

from plaso.formatters import interface
from plaso.formatters import manager
from plaso.lib import errors


class ChromeExtensionActivityEventFormatter(
    interface.ConditionalEventFormatter):
  """Formatter for a Chrome extension activity event."""

  DATA_TYPE = u'chrome:extension_activity:activity_log'

  FORMAT_STRING_PIECES = [
      u'Chrome extension: {extension_id}',
      u'Action type: {action_type}',
      u'Activity identifier: {activity_id}',
      u'Page URL: {page_url}',
      u'Page title: {page_title}',
      u'API name: {api_name}',
      u'Args: {args}',
      u'Other: {other}']

  FORMAT_STRING_SHORT_PIECES = [
      u'{extension_id}',
      u'{api_name}',
      u'{args}']

  SOURCE_LONG = u'Chrome Extension Activity'
  SOURCE_SHORT = u'WEBHIST'

  # From:
  # https://chromium.googlesource.com/chromium/src.git/+/master/chrome/browser/extensions/activity_log/activity_actions.h
  _CHROME_ACTION_TYPES = {
      0 : "API call",
      1 : "API event callback",
      2 : "API action blocked",
      3 : "Content Script inserted",
      4 : "DOM access",
      5 : "DOM event",
      6 : "WebRequest",
      1001 : "Unspecified"
  }

  def GetMessages(self, unused_formatter_mediator, event_object):
    """Determines the formatted message strings for an event object.

    Args:
      formatter_mediator: the formatter mediator object (instance of
                          FormatterMediator).
      event_object: the event object (instance of EventObject).

    Returns:
      A tuple containing the formatted message string and short message string.

    Raises:
      WrongFormatter: if the event object cannot be formatted by the formatter.
    """
    if self.DATA_TYPE != event_object.data_type:
      raise errors.WrongFormatter(u'Unsupported data type: {0:s}.'.format(
          event_object.data_type))

    event_values = event_object.GetValues()

    action_type = event_values.get(u'action_type')
    event_values[u'action_type'] = u'%s (type %d)'%(
        self._CHROME_ACTION_TYPES.get(action_type, "unknown action_type"),
        action_type
    )

    return self._ConditionalFormatMessages(event_values)



manager.FormattersManager.RegisterFormatter(
    ChromeExtensionActivityEventFormatter)
