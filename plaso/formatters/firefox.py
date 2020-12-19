# -*- coding: utf-8 -*-
"""The Mozilla Firefox history event formatter."""

from __future__ import unicode_literals

from plaso.formatters import interface
from plaso.formatters import manager


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

  def FormatEventValues(self, event_values):
    """Formats event values using the helpers.

    Args:
      event_values (dict[str, object]): event values.
    """
    visit_type = event_values.get('visit_type', 0)

    extras = []
    from_visit = event_values.get('from_visit', '')
    if from_visit:
      extras.append('visited from: {0:s}'.format(from_visit))

    hidden = event_values.get('hidden', '')
    if hidden == '1':
      extras.append('(url hidden)')

    typed = event_values.get('typed', '')
    if typed == '1':
      extras.append('(directly typed)')
    else:
      extras.append('(URL not typed directly)')

    transition = self._URL_TRANSITIONS.get(visit_type, None)
    if transition:
      transition_str = 'Transition: {0!s}'.format(transition)
      extras.append(transition_str)

    event_values['extra_string'] = ' '.join(extras)


manager.FormattersManager.RegisterFormatter(FirefoxPageVisitFormatter)
