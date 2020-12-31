# -*- coding: utf-8 -*-
"""Mozilla Firefox history custom event formatter helpers."""

from __future__ import unicode_literals

from plaso.formatters import interface
from plaso.formatters import manager


class FirefoxPageVisitFormatter(interface.CustomEventFormatterHelper):
  """Custom formatter for Firefox page visited event values."""

  DATA_TYPE = 'firefox:places:page_visited'

  def FormatEventValues(self, event_values):
    """Formats event values using the helper.

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


manager.FormattersManager.RegisterEventFormatterHelper(
    FirefoxPageVisitFormatter)
