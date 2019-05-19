# -*- coding: utf-8 -*-
"""The MacOS Notification Center event formatter."""

from __future__ import unicode_literals

from plaso.formatters import interface
from plaso.formatters import manager
from plaso.lib import errors

class MacNotificationCenterFormatter(interface.ConditionalEventFormatter):
  """Formatter for a MacOS Notification Center event. """

  DATA_TYPE = 'mac:notificationcenter:db'

  FORMAT_STRING_PIECES = [
      'Title: {title}',
      '(, subtitle: {subtitle}),',
      'registered by: {bundle_name}.',
      'Presented: {presented},',
      'Content: {body}']

  FORMAT_STRING_SHORT_PIECES = [
      'Title: {title},',
      'Content: {body}']

  SOURCE_LONG = 'Notification Center'
  SOURCE_SHORT = 'NOTIFICATION'

  _BOOLEAN_PRETTY_PRINT = {
      0: 'No',
      1: 'Yes'
  }

  # pylint: disable=unused-argument
  def GetMessages(self, formatter_mediator, event_data):
    """Determines the formatted message strings for the event data.

    Args:
      formatter_mediator (FormatterMediator): mediates the interactions between
          formatters and other components
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

    presented = event_values.get('presented', None)
    if presented is not None:
      event_values['presented'] = (
          self._BOOLEAN_PRETTY_PRINT.get(presented, 'UNKNOWN'))

    return self._ConditionalFormatMessages(event_values)

manager.FormattersManager.RegisterFormatter(MacNotificationCenterFormatter)
