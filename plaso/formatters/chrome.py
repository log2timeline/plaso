# -*- coding: utf-8 -*-
"""The Google Chrome history event formatters."""

from plaso.formatters import interface
from plaso.formatters import manager


class ChromeFileDownloadFormatter(interface.ConditionalEventFormatter):
  """Formatter for a Chrome file download event."""

  DATA_TYPE = 'chrome:history:file_downloaded'

  FORMAT_STRING_PIECES = [
      u'{url}',
      u'({full_path}).',
      u'Received: {received_bytes} bytes',
      u'out of: {total_bytes} bytes.']

  FORMAT_STRING_SHORT_PIECES = [
      u'{full_path} downloaded',
      u'({received_bytes} bytes)']

  SOURCE_LONG = 'Chrome History'
  SOURCE_SHORT = 'WEBHIST'


class ChromePageVisitedFormatter(interface.ConditionalEventFormatter):
  """Formatter for a Chrome page visited event."""

  DATA_TYPE = 'chrome:history:page_visited'

  FORMAT_STRING_PIECES = [
      u'{url}',
      u'({title})',
      u'[count: {typed_count}]',
      u'Host: {host}',
      u'Visit from: {from_visit}',
      u'Visit Source: [{visit_source}]',
      u'{extra}']

  FORMAT_STRING_SHORT_PIECES = [
      u'{url}',
      u'({title})']

  SOURCE_LONG = 'Chrome History'
  SOURCE_SHORT = 'WEBHIST'


manager.FormattersManager.RegisterFormatters([
    ChromeFileDownloadFormatter, ChromePageVisitedFormatter])
