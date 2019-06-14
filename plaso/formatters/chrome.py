# -*- coding: utf-8 -*-
"""The Google Chrome history event formatters."""

from __future__ import unicode_literals

from plaso.formatters import interface
from plaso.formatters import manager
from plaso.lib import errors


class ChromeFileDownloadFormatter(interface.ConditionalEventFormatter):
  """Formatter for a Chrome file download event."""

  DATA_TYPE = 'chrome:history:file_downloaded'

  FORMAT_STRING_PIECES = [
      '{url}',
      '({full_path}).',
      'Received: {received_bytes} bytes',
      'out of: {total_bytes} bytes.']

  FORMAT_STRING_SHORT_PIECES = [
      '{full_path} downloaded',
      '({received_bytes} bytes)']

  SOURCE_LONG = 'Chrome History'
  SOURCE_SHORT = 'WEBHIST'


class ChromePageVisitedFormatter(interface.ConditionalEventFormatter):
  """Formatter for a Chrome page visited event."""

  DATA_TYPE = 'chrome:history:page_visited'

  FORMAT_STRING_PIECES = [
      '{url}',
      '({title})',
      '[count: {typed_count}]',
      'Visit from: {from_visit}',
      'Visit Source: [{visit_source}]',
      'Type: [{page_transition}]',
      '{extra}']

  FORMAT_STRING_SHORT_PIECES = [
      '{url}',
      '({title})']

  SOURCE_LONG = 'Chrome History'
  SOURCE_SHORT = 'WEBHIST'

  _UNKNOWN_PAGE_TRANSITION = ('UNKNOWN', None)
  # The following definition for values can be found here:
  # https://cs.chromium.org/chromium/src/ui/base/page_transition_types.h
  _PAGE_TRANSITIONS = {
      0: ('LINK', 'User clicked a link'),
      1: ('TYPED', 'User typed the URL in the URL bar'),
      2: ('AUTO_BOOKMARK', 'Got through a suggestion in the UI'),
      3: ('AUTO_SUBFRAME',
          ('Content automatically loaded in a non-toplevel frame - user may not'
           'realize')),
      4: ('MANUAL_SUBFRAME', 'Subframe explicitly requested by the user'),
      5: ('GENERATED',
          ('User typed in the URL bar and selected an entry from the list - '
           'such as a search bar')),
      6: ('START_PAGE', 'The start page of the browser'),
      7: ('FORM_SUBMIT', 'A form the user has submitted values to'),
      8: ('RELOAD',
          ('The user reloaded the page, eg by hitting the reload button or '
           'restored a session')),
      9: ('KEYWORD',
          ('URL what was generated from a replaceable keyword other than the '
           'default search provider')),
      10: ('KEYWORD_GENERATED',
           'Corresponds to a visit generated from a KEYWORD')}

  # The following is the values for the source enum found in the visit_source
  # table and describes where a record originated from (if it originates from a
  # different storage than locally generated). The source can be found here:
  # https://cs.chromium.org/chromium/src/ui/app_list/search/history_types.h
  _VISIT_SOURCE = {
      0: 'SOURCE_SYNCED',
      1: 'SOURCE_BROWSED',
      2: 'SOURCE_EXTENSION',
      3: 'SOURCE_FIREFOX_IMPORTED',
      4: 'SOURCE_IE_IMPORTED',
      5: 'SOURCE_SAFARI_IMPORTED'}

  # pylint: disable=unused-argument
  def GetMessages(self, formatter_mediator, event_data):
    """Determines the formatted message strings for the event data.

    Args:
      formatter_mediator (FormatterMediator): mediates the interactions between
          formatters and other components, such as storage and Windows EventLog
          resources.
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

    page_transition_type = event_values.get('page_transition_type', None)
    if page_transition_type is not None:
      page_transition, page_transition_long = self._PAGE_TRANSITIONS.get(
          page_transition_type, self._UNKNOWN_PAGE_TRANSITION)

      if page_transition_long:
        event_values['page_transition'] = '{0:s} - {1:s}'.format(
            page_transition, page_transition_long)
      else:
        event_values['page_transition'] = page_transition

    visit_source = event_values.get('visit_source', None)
    if visit_source is not None:
      event_values['visit_source'] = self._VISIT_SOURCE.get(
          visit_source, 'UNKNOWN')

    extras = []

    url_hidden = event_values.get('url_hidden', False)
    if url_hidden:
      extras.append('(url hidden)')

    typed_count = event_values.get('typed_count', 0)
    if typed_count == 0:
      extras.append('(URL not typed directly - no typed count)')
    elif typed_count == 1:
      extras.append('(type count {0:d} time)'.format(typed_count))
    else:
      extras.append('(type count {0:d} times)'.format(typed_count))

    event_values['extra'] = ' '.join(extras)

    return self._ConditionalFormatMessages(event_values)


manager.FormattersManager.RegisterFormatters([
    ChromeFileDownloadFormatter, ChromePageVisitedFormatter])
