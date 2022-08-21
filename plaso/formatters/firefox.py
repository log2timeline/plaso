# -*- coding: utf-8 -*-
"""Mozilla Firefox history custom event formatter helpers."""

from plaso.formatters import interface
from plaso.formatters import manager


class FirefoxHistoryTypedCountFormatterHelper(
    interface.CustomEventFormatterHelper):
  """Mozilla Firefox history typed count formatter helper."""

  IDENTIFIER = 'firefox_history_typed_count'

  def FormatEventValues(self, output_mediator, event_values):
    """Formats event values using the helper.

    Args:
      output_mediator (OutputMediator): output mediator.
      event_values (dict[str, object]): event values.
    """
    typed = event_values.get('typed', None)
    if typed == '1':
      url_typed_string = '(URL directly typed)'
    else:
      url_typed_string = '(URL not typed directly)'

    event_values['url_typed_string'] = url_typed_string


class FirefoxHistoryURLHiddenFormatterHelper(
    interface.CustomEventFormatterHelper):
  """Mozilla Firefox history URL hidden formatter helper."""

  IDENTIFIER = 'firefox_history_url_hidden'

  def FormatEventValues(self, output_mediator, event_values):
    """Formats event values using the helper.

    Args:
      output_mediator (OutputMediator): output mediator.
      event_values (dict[str, object]): event values.
    """
    hidden = event_values.get('hidden', None)
    if hidden == '1':
      event_values['url_hidden_string'] = '(URL hidden)'


manager.FormattersManager.RegisterEventFormatterHelpers([
    FirefoxHistoryTypedCountFormatterHelper,
    FirefoxHistoryURLHiddenFormatterHelper])
