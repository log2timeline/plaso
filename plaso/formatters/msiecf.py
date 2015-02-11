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
      u'HTTP headers: {http_headers_cleaned}',
      u'{recovered_string}']

  FORMAT_STRING_SHORT_PIECES = [
      u'Location: {url}']

  SOURCE_LONG = 'MSIE Cache File URL record'
  SOURCE_SHORT = 'WEBHIST'

  def GetMessages(self, event_object):
    """Returns a list of messages extracted from an event object.

    Args:
      event_object: The event object (EventObject) containing the event
                    specific data.

    Returns:
      A list that contains both the longer and shorter version of the message
      string.
    """
    if self.DATA_TYPE != event_object.data_type:
      raise errors.WrongFormatter(u'Unsupported data type: {0:s}.'.format(
          event_object.data_type))

    if hasattr(event_object, 'http_headers'):
      event_object.http_headers_cleaned = event_object.http_headers.replace(
          '\r\n', ' - ')
    # TODO: Could this be moved upstream since this is done in other parsers
    # as well?
    if getattr(event_object, 'recovered', None):
      event_object.recovered_string = '[Recovered Entry]'

    return super(MsiecfUrlFormatter, self).GetMessages(event_object)


manager.FormattersManager.RegisterFormatter(MsiecfUrlFormatter)
