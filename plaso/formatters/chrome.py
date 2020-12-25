# -*- coding: utf-8 -*-
"""Google Chrome history custom event formatter helpers."""

from __future__ import unicode_literals

from plaso.formatters import interface
from plaso.formatters import manager


class ChromePageVisitedFormatter(interface.CustomEventFormatterHelper):
  """Custom formatter for Chrome page visited event values."""

  DATA_TYPE = 'chrome:history:page_visited'

  def FormatEventValues(self, event_values):
    """Formats event values using the helper.

    Args:
      event_values (dict[str, object]): event values.
    """
    typed_count = event_values.get('typed_count', 0)
    if typed_count == 0:
      url_typed_string = '(URL not typed directly)'
    elif typed_count == 1:
      url_typed_string = '(URL typed {0:d} time)'
    else:
      url_typed_string = '(URL typed {0:d} times)'

    event_values['url_typed_string'] = url_typed_string


manager.FormattersManager.RegisterEventFormatterHelper(
    ChromePageVisitedFormatter)
