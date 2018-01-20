# -*- coding: utf-8 -*-
"""The MSIE WebCache ESE database event formatters."""

from __future__ import unicode_literals

from plaso.formatters import interface
from plaso.formatters import manager


class MsieWebCacheContainerEventFormatter(interface.ConditionalEventFormatter):
  """Formatter for a MSIE WebCache ESE database Container_# table record."""

  DATA_TYPE = 'msie:webcache:container'

  FORMAT_STRING_PIECES = [
      'URL: {url}',
      'Redirect URL: {redirect_url}',
      'Access count: {access_count}',
      'Sync count: {sync_count}',
      'Filename: {cached_filename}',
      'File extension: {file_extension}',
      'Cached file size: {cached_file_size}',
      'Request headers: {request_headers}',
      'Response headers: {response_headers}',
      'Entry identifier: {entry_identifier}',
      'Container identifier: {container_identifier}',
      'Cache identifier: {cache_identifier}']

  FORMAT_STRING_SHORT_PIECES = [
      'URL: {url}']

  SOURCE_LONG = 'MSIE WebCache container record'
  SOURCE_SHORT = 'WEBHIST'


class MsieWebCacheContainersEventFormatter(interface.ConditionalEventFormatter):
  """Formatter for a MSIE WebCache ESE database Containers table record."""

  DATA_TYPE = 'msie:webcache:containers'

  FORMAT_STRING_PIECES = [
      'Name: {name}',
      'Directory: {directory}',
      'Table: Container_{container_identifier}',
      'Container identifier: {container_identifier}',
      'Set identifier: {set_identifier}']

  FORMAT_STRING_SHORT_PIECES = [
      'Directory: {directory}']

  SOURCE_LONG = 'MSIE WebCache containers record'
  SOURCE_SHORT = 'WEBHIST'


class MsieWebCacheLeakFilesEventFormatter(interface.ConditionalEventFormatter):
  """Formatter for a MSIE WebCache ESE database LeakFiles table record."""

  DATA_TYPE = 'msie:webcache:leak_file'

  FORMAT_STRING_PIECES = [
      'Filename: {cached_filename}',
      'Leak identifier: {leak_identifier}']

  FORMAT_STRING_SHORT_PIECES = [
      'Filename: {cached_filename}']

  SOURCE_LONG = 'MSIE WebCache partitions record'
  SOURCE_SHORT = 'WEBHIST'


class MsieWebCachePartitionsEventFormatter(interface.ConditionalEventFormatter):
  """Formatter for a MSIE WebCache ESE database Partitions table record."""

  DATA_TYPE = 'msie:webcache:partitions'

  FORMAT_STRING_PIECES = [
      'Partition identifier: {partition_identifier}',
      'Partition type: {partition_type}',
      'Directory: {directory}',
      'Table identifier: {table_identifier}']

  FORMAT_STRING_SHORT_PIECES = [
      'Directory: {directory}']

  SOURCE_LONG = 'MSIE WebCache partitions record'
  SOURCE_SHORT = 'WEBHIST'


manager.FormattersManager.RegisterFormatters([
    MsieWebCacheContainerEventFormatter, MsieWebCacheContainersEventFormatter,
    MsieWebCacheLeakFilesEventFormatter, MsieWebCachePartitionsEventFormatter])
