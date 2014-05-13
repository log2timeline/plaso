#!/usr/bin/python
# -*- coding: utf-8 -*-
#
# Copyright 2014 The Plaso Project Authors.
# Please see the AUTHORS file for details on individual authors.
#
# Licensed under the Apache License, Version 2.0 (the "License");
# you may not use this file except in compliance with the License.
# You may obtain a copy of the License at
#
#    http://www.apache.org/licenses/LICENSE-2.0
#
# Unless required by applicable law or agreed to in writing, software
# distributed under the License is distributed on an "AS IS" BASIS,
# WITHOUT WARRANTIES OR CONDITIONS OF ANY KIND, either express or implied.
# See the License for the specific language governing permissions and
# limitations under the License.
"""Formatters for the MSIE WebCache ESE database events."""

from plaso.lib import eventdata


class MsieWebCacheContainerEventFormatter(eventdata.ConditionalEventFormatter):
  """Formatter for a MSIE WebCache ESE database Container_# table record."""
  DATA_TYPE = 'msie:webcache:container'

  FORMAT_STRING_PIECES = [
      u'Entry identifier: {entry_identifier}',
      u'Container identifier: {container_identifier}',
      u'Cache identifier: {cache_identifier}',
      u'URL: {url}',
      u'Redirect URL: {redirect_url}',
      u'Access count: {access_count}',
      u'Sync count: {sync_count}',
      u'Filename: {cached_filename}',
      u'File extension: {file_extension}',
      u'Cached file size: {cached_file_size}',
      u'Request headers: {request_headers}',
      u'Response headers: {response_headers}']

  FORMAT_STRING_SHORT_PIECES = [
      u'URL: {url}']

  SOURCE_LONG = 'MSIE WebCache container record'
  SOURCE_SHORT = 'WEBHIST'


class MsieWebCacheContainersEventFormatter(eventdata.ConditionalEventFormatter):
  """Formatter for a MSIE WebCache ESE database Containers table record."""
  DATA_TYPE = 'msie:webcache:containers'

  FORMAT_STRING_PIECES = [
      u'Container identifier: {container_identifier}',
      u'Set identifier: {set_identifier}',
      u'Name: {name}',
      u'Directory: {directory}',
      u'Table: Container_{container_identifier}']

  FORMAT_STRING_SHORT_PIECES = [
      u'Directory: {directory}']

  SOURCE_LONG = 'MSIE WebCache containers record'
  SOURCE_SHORT = 'WEBHIST'


class MsieWebCacheLeakFilesEventFormatter(eventdata.ConditionalEventFormatter):
  """Formatter for a MSIE WebCache ESE database LeakFiles table record."""
  DATA_TYPE = 'msie:webcache:leak_file'

  FORMAT_STRING_PIECES = [
      u'Leak identifier: {leak_identifier}',
      u'Filename: {cached_filename}']

  FORMAT_STRING_SHORT_PIECES = [
      u'Filename: {cached_filename}']

  SOURCE_LONG = 'MSIE WebCache partitions record'
  SOURCE_SHORT = 'WEBHIST'


class MsieWebCachePartitionsEventFormatter(eventdata.ConditionalEventFormatter):
  """Formatter for a MSIE WebCache ESE database Partitions table record."""
  DATA_TYPE = 'msie:webcache:partitions'

  FORMAT_STRING_PIECES = [
      u'Partition identifier: {partition_identifier}',
      u'Partition type: {partition_type}',
      u'Directory: {directory}',
      u'Table identifier: {table_identifier}']

  FORMAT_STRING_SHORT_PIECES = [
      u'Directory: {directory}']

  SOURCE_LONG = 'MSIE WebCache partitions record'
  SOURCE_SHORT = 'WEBHIST'
