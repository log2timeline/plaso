# -*- coding: utf-8 -*-
"""The Google Chrome history event formatters."""

from __future__ import unicode_literals

from plaso.formatters import interface
from plaso.formatters import manager


class ChromeFileDownloadFormatter(interface.ConditionalEventFormatter):
  """Formatter for a Chrome file download event."""

  DATA_TYPE = 'chrome:history:file_downloaded'

  FORMAT_STRING_PIECES = [
      '{url}',
      '({full_path}).',
      'Received: {received_bytes} bytes',
      'out of: {total_bytes} bytes.']

  FORMAT_STRING_SHORT_PIECES = [
      '{full_path} downloaded',
      '({received_bytes} bytes)']

  SOURCE_LONG = 'Chrome History'
  SOURCE_SHORT = 'WEBHIST'


class ChromePageVisitedFormatter(interface.ConditionalEventFormatter):
  """Formatter for a Chrome page visited event."""

  DATA_TYPE = 'chrome:history:page_visited'

  FORMAT_STRING_PIECES = [
      '{url}',
      '({title})',
      '[count: {typed_count}]',
      'Visit from: {from_visit}',
      'Visit Source: [{visit_source}]',
      '{extra}']

  FORMAT_STRING_SHORT_PIECES = [
      '{url}',
      '({title})']

  SOURCE_LONG = 'Chrome History'
  SOURCE_SHORT = 'WEBHIST'


manager.FormattersManager.RegisterFormatters([
    ChromeFileDownloadFormatter, ChromePageVisitedFormatter])
