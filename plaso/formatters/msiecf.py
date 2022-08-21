# -*- coding: utf-8 -*-
"""MSIE cache file custom event formatter helpers."""

from plaso.formatters import interface
from plaso.formatters import manager


class MSIECFCachedPathFormatterHelper(interface.CustomEventFormatterHelper):
  """MSIE cache file cached path formatter helper."""

  IDENTIFIER = 'msiecf_cached_path'

  def FormatEventValues(self, output_mediator, event_values):
    """Formats event values using the helper.

    Args:
      output_mediator (OutputMediator): output mediator.
      event_values (dict[str, object]): event values.
    """
    cached_file_path = event_values.get('cached_filename', None)
    if cached_file_path:
      cache_directory_name = event_values.get('cache_directory_name', None)
      if cache_directory_name:
        cached_file_path = '\\'.join([cache_directory_name, cached_file_path])
      event_values['cached_file_path'] = cached_file_path


class MSIECFHTTPHeadersventFormatterHelper(
    interface.CustomEventFormatterHelper):
  """MSIE cache file HTTP headers formatter helper."""

  IDENTIFIER = 'msiecf_http_headers'

  def FormatEventValues(self, output_mediator, event_values):
    """Formats event values using the helper.

    Args:
      output_mediator (OutputMediator): output mediator.
      event_values (dict[str, object]): event values.
    """
    http_headers = event_values.get('http_headers', None)
    if http_headers:
      event_values['http_headers'] = http_headers.replace('\r\n', ' - ')


manager.FormattersManager.RegisterEventFormatterHelpers([
    MSIECFCachedPathFormatterHelper, MSIECFHTTPHeadersventFormatterHelper])
