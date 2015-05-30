# -*- coding: utf-8 -*-
"""The Mozilla Firefox history event formatter."""

from plaso.formatters import interface
from plaso.formatters import manager
from plaso.lib import errors


class FirefoxBookmarkAnnotationFormatter(interface.ConditionalEventFormatter):
  """The Firefox bookmark annotation event formatter."""

  DATA_TYPE = u'firefox:places:bookmark_annotation'

  FORMAT_STRING_PIECES = [
      u'Bookmark Annotation: [{content}]',
      u'to bookmark [{title}]',
      u'({url})']

  FORMAT_STRING_SHORT_PIECES = [u'Bookmark Annotation: {title}']

  SOURCE_LONG = u'Firefox History'
  SOURCE_SHORT = u'WEBHIST'


class FirefoxBookmarkFolderFormatter(interface.EventFormatter):
  """The Firefox bookmark folder event formatter."""

  DATA_TYPE = u'firefox:places:bookmark_folder'

  FORMAT_STRING = u'{title}'

  SOURCE_LONG = u'Firefox History'
  SOURCE_SHORT = u'WEBHIST'


class FirefoxBookmarkFormatter(interface.ConditionalEventFormatter):
  """The Firefox URL bookmark event formatter."""

  DATA_TYPE = u'firefox:places:bookmark'

  FORMAT_STRING_PIECES = [
      u'Bookmark {type}',
      u'{title}',
      u'({url})',
      u'[{places_title}]',
      u'visit count {visit_count}']

  FORMAT_STRING_SHORT_PIECES = [
      u'Bookmarked {title}',
      u'({url})']

  SOURCE_LONG = u'Firefox History'
  SOURCE_SHORT = u'WEBHIST'


class FirefoxPageVisitFormatter(interface.ConditionalEventFormatter):
  """The Firefox page visited event formatter."""

  DATA_TYPE = u'firefox:places:page_visited'

  # Transitions defined in the source file:
  #   src/toolkit/components/places/nsINavHistoryService.idl
  # Also contains further explanation into what each of these settings mean.
  _URL_TRANSITIONS = {
      1: u'LINK',
      2: u'TYPED',
      3: u'BOOKMARK',
      4: u'EMBED',
      5: u'REDIRECT_PERMANENT',
      6: u'REDIRECT_TEMPORARY',
      7: u'DOWNLOAD',
      8: u'FRAMED_LINK',
  }
  _URL_TRANSITIONS.setdefault(u'UNKOWN')

  # TODO: Make extra conditional formatting.
  FORMAT_STRING_PIECES = [
      u'{url}',
      u'({title})',
      u'[count: {visit_count}]',
      u'Host: {host}',
      u'{extra_string}']

  FORMAT_STRING_SHORT_PIECES = [u'URL: {url}']

  SOURCE_LONG = u'Firefox History'
  SOURCE_SHORT = u'WEBHIST'

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

    visit_type = event_values.get(u'visit_type', 0)
    transition = self._URL_TRANSITIONS.get(visit_type, None)
    if transition:
      transition_str = u'Transition: {0!s}'.format(transition)

    extra = event_values.get(u'extra', None)
    if extra:
      if transition:
        extra.append(transition_str)
      event_values[u'extra_string'] = u' '.join(extra)

    elif transition:
      event_values[u'extra_string'] = transition_str

    return self._ConditionalFormatMessages(event_values)


class FirefoxDowloadFormatter(interface.EventFormatter):
  """The Firefox download event formatter."""

  DATA_TYPE = u'firefox:downloads:download'

  FORMAT_STRING = (
      u'{url} ({full_path}). Received: {received_bytes} bytes '
      u'out of: {total_bytes} bytes.')
  FORMAT_STRING_SHORT = u'{full_path} downloaded ({received_bytes} bytes)'

  SOURCE_LONG = u'Firefox History'
  SOURCE_SHORT = u'WEBHIST'


manager.FormattersManager.RegisterFormatters([
    FirefoxBookmarkAnnotationFormatter, FirefoxBookmarkFolderFormatter,
    FirefoxBookmarkFormatter, FirefoxPageVisitFormatter,
    FirefoxDowloadFormatter])
