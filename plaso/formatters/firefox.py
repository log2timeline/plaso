# -*- coding: utf-8 -*-
"""The Mozilla Firefox history event formatter."""

from __future__ import unicode_literals

from plaso.formatters import interface
from plaso.formatters import manager
from plaso.lib import errors


class FirefoxBookmarkAnnotationFormatter(interface.ConditionalEventFormatter):
  """The Firefox bookmark annotation event formatter."""

  DATA_TYPE = 'firefox:places:bookmark_annotation'

  FORMAT_STRING_PIECES = [
      'Bookmark Annotation: [{content}]',
      'to bookmark [{title}]',
      '({url})']

  FORMAT_STRING_SHORT_PIECES = ['Bookmark Annotation: {title}']

  SOURCE_LONG = 'Firefox History'
  SOURCE_SHORT = 'WEBHIST'


class FirefoxBookmarkFolderFormatter(interface.EventFormatter):
  """The Firefox bookmark folder event formatter."""

  DATA_TYPE = 'firefox:places:bookmark_folder'

  FORMAT_STRING = '{title}'

  SOURCE_LONG = 'Firefox History'
  SOURCE_SHORT = 'WEBHIST'


class FirefoxBookmarkFormatter(interface.ConditionalEventFormatter):
  """The Firefox URL bookmark event formatter."""

  DATA_TYPE = 'firefox:places:bookmark'

  FORMAT_STRING_PIECES = [
      'Bookmark {type}',
      '{title}',
      '({url})',
      '[{places_title}]',
      'visit count {visit_count}']

  FORMAT_STRING_SHORT_PIECES = [
      'Bookmarked {title}',
      '({url})']

  SOURCE_LONG = 'Firefox History'
  SOURCE_SHORT = 'WEBHIST'


class FirefoxPageVisitFormatter(interface.ConditionalEventFormatter):
  """The Firefox page visited event formatter."""

  DATA_TYPE = 'firefox:places:page_visited'

  # Transitions defined in the source file:
  #   src/toolkit/components/places/nsINavHistoryService.idl
  # Also contains further explanation into what each of these settings mean.
  _URL_TRANSITIONS = {
      1: 'LINK',
      2: 'TYPED',
      3: 'BOOKMARK',
      4: 'EMBED',
      5: 'REDIRECT_PERMANENT',
      6: 'REDIRECT_TEMPORARY',
      7: 'DOWNLOAD',
      8: 'FRAMED_LINK',
  }
  _URL_TRANSITIONS.setdefault('UNKOWN')

  # TODO: Make extra conditional formatting.
  FORMAT_STRING_PIECES = [
      '{url}',
      '({title})',
      '[count: {visit_count}]',
      'Host: {host}',
      '{extra_string}']

  FORMAT_STRING_SHORT_PIECES = ['URL: {url}']

  SOURCE_LONG = 'Firefox History'
  SOURCE_SHORT = 'WEBHIST'

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

    visit_type = event_values.get('visit_type', 0)
    transition = self._URL_TRANSITIONS.get(visit_type, None)
    if transition:
      transition_str = 'Transition: {0!s}'.format(transition)

    extra = event_values.get('extra', None)
    if extra:
      if transition:
        extra.append(transition_str)
      event_values['extra_string'] = ' '.join(extra)

    elif transition:
      event_values['extra_string'] = transition_str

    return self._ConditionalFormatMessages(event_values)


class FirefoxDowloadFormatter(interface.EventFormatter):
  """The Firefox download event formatter."""

  DATA_TYPE = 'firefox:downloads:download'

  FORMAT_STRING = (
      '{url} ({full_path}). Received: {received_bytes} bytes '
      'out of: {total_bytes} bytes.')
  FORMAT_STRING_SHORT = '{full_path} downloaded ({received_bytes} bytes)'

  SOURCE_LONG = 'Firefox History'
  SOURCE_SHORT = 'WEBHIST'


manager.FormattersManager.RegisterFormatters([
    FirefoxBookmarkAnnotationFormatter, FirefoxBookmarkFolderFormatter,
    FirefoxBookmarkFormatter, FirefoxPageVisitFormatter,
    FirefoxDowloadFormatter])
