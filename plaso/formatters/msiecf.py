# -*- coding: utf-8 -*-
"""The Microsoft Internet Explorer (MSIE) Cache Files (CF) event formatters."""

from __future__ import unicode_literals

from plaso.formatters import interface
from plaso.formatters import manager


class MsiecfItemFormatter(interface.ConditionalEventFormatter):
  """Formatter for a MSIECF item event."""

  def FormatEventValues(self, event_values):
    """Formats event values using the helpers.

    Args:
      event_values (dict[str, object]): event values.
    """
    http_headers = event_values.get('http_headers', None)
    if http_headers:
      event_values['http_headers'] = http_headers.replace('\r\n', ' - ')

    if event_values.get('recovered', None):
      event_values['recovered_string'] = '[Recovered Entry]'

    cached_file_path = event_values.get('cached_filename', None)
    if cached_file_path:
      cache_directory_name = event_values.get('cache_directory_name', None)
      if cache_directory_name:
        cached_file_path = '\\'.join([cache_directory_name, cached_file_path])
      event_values['cached_file_path'] = cached_file_path


class MsiecfLeakFormatter(MsiecfItemFormatter):
  """Formatter for a MSIECF leak item event."""

  DATA_TYPE = 'msiecf:leak'

  FORMAT_STRING_PIECES = [
      'Cached file: {cached_file_path}',
      'Cached file size: {cached_file_size}',
      '{recovered_string}']

  FORMAT_STRING_SHORT_PIECES = [
      'Cached file: {cached_file_path}']


class MsiecfRedirectedFormatter(MsiecfItemFormatter):
  """Formatter for a MSIECF leak redirected event."""

  DATA_TYPE = 'msiecf:redirected'

  FORMAT_STRING_PIECES = [
      'Location: {url}',
      '{recovered_string}']

  FORMAT_STRING_SHORT_PIECES = [
      'Location: {url}']


class MsiecfUrlFormatter(MsiecfItemFormatter):
  """Formatter for a MSIECF URL item event."""

  DATA_TYPE = 'msiecf:url'

  FORMAT_STRING_PIECES = [
      'Location: {url}',
      'Number of hits: {number_of_hits}',
      'Cached file: {cached_file_path}',
      'Cached file size: {cached_file_size}',
      'HTTP headers: {http_headers}',
      '{recovered_string}']

  FORMAT_STRING_SHORT_PIECES = [
      'Location: {url}',
      'Cached file: {cached_file_path}']


manager.FormattersManager.RegisterFormatters([
    MsiecfLeakFormatter, MsiecfRedirectedFormatter, MsiecfUrlFormatter])
