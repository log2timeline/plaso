# -*- coding: utf-8 -*-
"""The Microsoft Internet Explorer (MSIE) Cache Files (CF) event formatters."""

from plaso.formatters import interface
from plaso.formatters import manager
from plaso.lib import errors


class MsiecfItemFormatter(interface.ConditionalEventFormatter):
  """Formatter for a MSIECF item event."""

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

    event_values = event_object.CopyToDict()

    http_headers = event_values.get(u'http_headers', None)
    if http_headers:
      event_values[u'http_headers'] = http_headers.replace(u'\r\n', u' - ')

    if event_values.get(u'recovered', None):
      event_values[u'recovered_string'] = u'[Recovered Entry]'

    cached_file_path = event_values.get(u'cached_filename', None)
    if cached_file_path:
      cache_directory_name = event_values.get(u'cache_directory_name', None)
      if cache_directory_name:
        cached_file_path = u'\\'.join([cache_directory_name, cached_file_path])
      event_values[u'cached_file_path'] = cached_file_path

    return self._ConditionalFormatMessages(event_values)


class MsiecfLeakFormatter(MsiecfItemFormatter):
  """Formatter for a MSIECF leak item event."""

  DATA_TYPE = u'msiecf:leak'

  FORMAT_STRING_PIECES = [
      u'Cached file: {cached_file_path}',
      u'Cached file size: {cached_file_size}',
      u'{recovered_string}']

  FORMAT_STRING_SHORT_PIECES = [
      u'Cached file: {cached_file_path}']

  SOURCE_LONG = u'MSIE Cache File leak record'
  SOURCE_SHORT = u'WEBHIST'


class MsiecfRedirectedFormatter(MsiecfItemFormatter):
  """Formatter for a MSIECF leak redirected event."""

  DATA_TYPE = u'msiecf:redirected'

  FORMAT_STRING_PIECES = [
      u'Location: {url}',
      u'{recovered_string}']

  FORMAT_STRING_SHORT_PIECES = [
      u'Location: {url}']

  SOURCE_LONG = u'MSIE Cache File redirected record'
  SOURCE_SHORT = u'WEBHIST'


class MsiecfUrlFormatter(MsiecfItemFormatter):
  """Formatter for a MSIECF URL item event."""

  DATA_TYPE = u'msiecf:url'

  FORMAT_STRING_PIECES = [
      u'Location: {url}',
      u'Number of hits: {number_of_hits}',
      u'Cached file: {cached_file_path}',
      u'Cached file size: {cached_file_size}',
      u'HTTP headers: {http_headers}',
      u'{recovered_string}']

  FORMAT_STRING_SHORT_PIECES = [
      u'Location: {url}',
      u'Cached file: {cached_file_path}']

  SOURCE_LONG = u'MSIE Cache File URL record'
  SOURCE_SHORT = u'WEBHIST'


manager.FormattersManager.RegisterFormatters([
    MsiecfLeakFormatter, MsiecfRedirectedFormatter, MsiecfUrlFormatter])
