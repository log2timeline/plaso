# -*- coding: utf-8 -*-
"""Google Chrome history custom event formatter helpers."""

from plaso.formatters import interface
from plaso.formatters import manager


class ChromeHistoryTypedCountFormatterHelper(
    interface.CustomEventFormatterHelper):
  """Google Chrome history typed count formatter helper."""

  IDENTIFIER = 'chrome_history_typed_count'

  def FormatEventValues(self, output_mediator, event_values):
    """Formats event values using the helper.

    Args:
      output_mediator (OutputMediator): output mediator.
      event_values (dict[str, object]): event values.
    """
    typed_count = event_values.get('typed_count', None)
    if typed_count is not None:
      if typed_count == 0:
        url_typed_string = '(URL not typed directly)'
      elif typed_count == 1:
        url_typed_string = '(URL typed 1 time)'
      elif typed_count > 1:
        url_typed_string = '(URL typed {0:d} times)'.format(typed_count)
      else:
        url_typed_string = typed_count

      event_values['url_typed_string'] = url_typed_string


manager.FormattersManager.RegisterEventFormatterHelper(
    ChromeHistoryTypedCountFormatterHelper)
