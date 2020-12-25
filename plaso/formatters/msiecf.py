# -*- coding: utf-8 -*-
"""Microsoft Internet Explorer (MSIE) custom event formatter helpers."""

from __future__ import unicode_literals

from plaso.formatters import interface
from plaso.formatters import manager


class MsiecfLeakFormatter(interface.CustomEventFormatterHelper):
  """Custom formatter for MSIE cache file leak item event values."""

  DATA_TYPE = 'msiecf:leak'

  def FormatEventValues(self, event_values):
    """Formats event values using the helper.

    Args:
      event_values (dict[str, object]): event values.
    """
    cached_file_path = event_values.get('cached_filename', None)
    if cached_file_path:
      cache_directory_name = event_values.get('cache_directory_name', None)
      if cache_directory_name:
        cached_file_path = '\\'.join([cache_directory_name, cached_file_path])
      event_values['cached_file_path'] = cached_file_path


class MsiecfUrlFormatter(interface.CustomEventFormatterHelper):
  """Custom formatter for MSIE cache file URL item event values."""

  DATA_TYPE = 'msiecf:url'

  def FormatEventValues(self, event_values):
    """Formats event values using the helper.

    Args:
      event_values (dict[str, object]): event values.
    """
    cached_file_path = event_values.get('cached_filename', None)
    if cached_file_path:
      cache_directory_name = event_values.get('cache_directory_name', None)
      if cache_directory_name:
        cached_file_path = '\\'.join([cache_directory_name, cached_file_path])
      event_values['cached_file_path'] = cached_file_path

    http_headers = event_values.get('http_headers', None)
    if http_headers:
      event_values['http_headers'] = http_headers.replace('\r\n', ' - ')


manager.FormattersManager.RegisterEventFormatterHelpers([
    MsiecfLeakFormatter, MsiecfUrlFormatter])
