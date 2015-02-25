# -*- coding: utf-8 -*-
"""Formatter for Microsoft Internet Explorer (MSIE) Cache Files (CF) events."""

from plaso.formatters import interface
from plaso.formatters import manager
from plaso.lib import errors


class MsiecfUrlFormatter(interface.ConditionalEventFormatter):
  """Formatter for a MSIECF URL item."""

  DATA_TYPE = 'msiecf:url'

  FORMAT_STRING_PIECES = [
      u'Location: {url}',
      u'Number of hits: {number_of_hits}',
      u'Cached file size: {cached_file_size}',
      u'HTTP headers: {http_headers}',
      u'{recovered_string}']

  FORMAT_STRING_SHORT_PIECES = [
      u'Location: {url}']

  SOURCE_LONG = 'MSIE Cache File URL record'
  SOURCE_SHORT = 'WEBHIST'

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

    http_headers = event_values.get(u'http_headers', None)
    if http_headers:
      event_values[u'http_headers'] = http_headers.replace(u'\r\n', u' - ')

    if event_values.get(u'recovered', None):
      event_values[u'recovered_string'] = '[Recovered Entry]'

    return self._ConditionalFormatMessages(event_values)


manager.FormattersManager.RegisterFormatter(MsiecfUrlFormatter)
