# -*- coding: utf-8 -*-
"""The Mozilla Firefox history event formatter."""

from __future__ import unicode_literals

from plaso.formatters import interface
from plaso.formatters import manager
from plaso.lib import errors


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


manager.FormattersManager.RegisterFormatter(FirefoxPageVisitFormatter)
