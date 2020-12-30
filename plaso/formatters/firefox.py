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

  FORMAT_STRING_PIECES = [
      '{url}',
      '({title})',
      '[count: {visit_count}]',
      'Host: {host}',
      'visited from: {from_visit}',
      '{url_hidden_string}',
      '{url_typed_string}',
      'Transition: {transition_string}']

  FORMAT_STRING_SHORT_PIECES = [
      'URL: {url}']

  def FormatEventValues(self, event_values):
    """Formats event values using the helpers.

    Args:
      event_values (dict[str, object]): event values.
    """
    hidden = event_values.get('hidden', None)
    if hidden == '1':
      event_values['url_hidden_string'] = '(URL hidden)'

    typed = event_values.get('typed', None)
    if typed == '1':
      url_typed_string = '(URL directly typed)'
    else:
      url_typed_string = '(URL not typed directly)'

    event_values['url_typed_string'] = url_typed_string

    visit_type = event_values.get('visit_type', 0)
    event_values['transition_string'] = self._URL_TRANSITIONS.get(
        visit_type, 'UNKOWN')


manager.FormattersManager.RegisterFormatter(FirefoxPageVisitFormatter)
