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
"""Parser for the Microsoft Internet Explorer WebCache ESE database.

The WebCache database (WebCacheV01.dat or WebCacheV24.dat) are used by MSIE
as of version 10.
"""

import logging

from plaso.events import time_events
from plaso.lib import eventdata
from plaso.parsers.esedb_plugins import interface


class MsieWebCacheContainersEventObject(time_events.FiletimeEvent):
  """Convenience class for a MSIE WebCache Containers table event."""

  DATA_TYPE = 'msie:webcache:containers'

  def __init__(self, timestamp, usage, record_values):
    """Initializes the event.

    Args:
      timestamp: The FILETIME timestamp value.
      usage: The usage string, describing the timestamp value.
      record_values: A dict object containing the record values.
    """
    super(MsieWebCacheContainersEventObject, self).__init__(timestamp, usage)

    self.container_identifier = record_values.get('ContainerId', 0)
    self.set_identifier = record_values.get('SetId', 0)
    self.name = record_values.get('Name', u'')
    self.directory = record_values.get('Directory', u'')


class MsieWebCacheContainerEventObject(time_events.FiletimeEvent):
  """Convenience class for a MSIE WebCache Container table event."""

  DATA_TYPE = 'msie:webcache:container'

  def __init__(self, timestamp, usage, record_values):
    """Initializes the event.

    Args:
      timestamp: The FILETIME timestamp value.
      usage: The usage string, describing the timestamp value.
      record_values: A dict object containing the record values.
    """
    super(MsieWebCacheContainerEventObject, self).__init__(timestamp, usage)

    self.entry_identifier = record_values.get(u'EntryId', 0)
    self.container_identifier = record_values.get(u'ContainerId', 0)
    self.cache_identifier = record_values.get(u'CacheId', 0)

    url = record_values.get(u'Url', u'')
    # Ignore URL that start with a binary value.
    if ord(url[0]) >= 0x20:
      self.url = url
    self.redirect_url = record_values.get(u'RedirectUrl', u'')

    self.access_count = record_values.get(u'AccessCount', 0)
    self.sync_count = record_values.get(u'SyncCount', 0)

    self.cached_filename = record_values.get('Filename', u'')
    self.file_extension = record_values.get(u'FileExtension', u'')
    self.cached_file_size = record_values.get(u'FileSize', 0)

    # Ignore non-Unicode request headers values.
    request_headers = record_values.get(u'RequestHeaders', u'')
    if type(request_headers) == unicode and request_headers:
      self.request_headers = request_headers

    # Ignore non-Unicode response headers values.
    response_headers = record_values.get(u'ResponseHeaders', u'')
    if type(response_headers) == unicode and response_headers:
      self.response_headers = response_headers


class MsieWebCacheLeakFilesEventObject(time_events.FiletimeEvent):
  """Convenience class for a MSIE WebCache LeakFiles table event."""

  DATA_TYPE = 'msie:webcache:leak_file'

  def __init__(self, timestamp, usage, record_values):
    """Initializes the event.

    Args:
      timestamp: The FILETIME timestamp value.
      usage: The usage string, describing the timestamp value.
      record_values: A dict object containing the record values.
    """
    super(MsieWebCacheLeakFilesEventObject, self).__init__(timestamp, usage)

    self.leak_identifier = record_values.get('LeakId', 0)
    self.cached_filename = record_values.get('Filename', u'')


class MsieWebCachePartitionsEventObject(time_events.FiletimeEvent):
  """Convenience class for a MSIE WebCache Partitions table event."""

  DATA_TYPE = 'msie:webcache:partitions'

  def __init__(self, timestamp, usage, record_values):
    """Initializes the event.

    Args:
      timestamp: The FILETIME timestamp value.
      usage: The usage string, describing the timestamp value.
      record_values: A dict object containing the record values.
    """
    super(MsieWebCachePartitionsEventObject, self).__init__(timestamp, usage)

    self.partition_identifier = record_values.get('PartitionId', 0)
    self.partition_type = record_values.get('PartitionType', 0)
    self.directory = record_values.get('Directory', u'')
    self.table_identifier = record_values.get('TableId', 0)


class MsieWebCacheEseDbPlugin(interface.EseDbPlugin):
  """Parses a MSIE WebCache ESE database file."""

  NAME = 'msie_webcache'

  # TODO: add support for AppCache_#, AppCacheEntry_#, DependencyEntry_#

  REQUIRED_TABLES = {
      'Containers': 'ParseContainersTable',
      'LeakFiles': 'ParseLeakFilesTable',
      'Partitions': 'ParsePartitionsTable'}

  _CONTAINER_TABLE_VALUE_MAPPINGS = {
      'RequestHeaders': '_ConvertValueBinaryDataToStringAscii',
      'ResponseHeaders': '_ConvertValueBinaryDataToStringAscii'}

  def _ParseContainerTable(self, table, container_name):
    """Parses a Container_# table.

    Args:
      table: The table object (instance of pyesedb.table).
      container_name: String that contains the container name.
                      The container name indicates the table type.

    Yields:
      An event object (instance of EventObject).
    """
    if table is None:
      logging.warning(u'[{0:s}] invalid Container_# table'.format(self.NAME))
      return

    for esedb_record in table.records:
      # TODO: add support for:
      # wpnidm, iecompat, iecompatua, DNTException, DOMStore
      if container_name == u'Content':
        value_mappings = self._CONTAINER_TABLE_VALUE_MAPPINGS
      else:
        value_mappings = None

      record_values = self._GetRecordValues(
          table.name, esedb_record, value_mappings=value_mappings)

      if (container_name in [
          u'Content', u'Cookies', u'History', u'iedownload'] or
          container_name.startswith(u'MSHist')):
        timestamp = record_values.get(u'SyncTime', 0)
        if timestamp:
          yield MsieWebCacheContainerEventObject(
              timestamp, u'Synchronization time', record_values)

        timestamp = record_values.get(u'CreationTime', 0)
        if timestamp:
          yield MsieWebCacheContainerEventObject(
              timestamp, eventdata.EventTimestamp.CREATION_TIME, record_values)

        timestamp = record_values.get(u'ExpiryTime', 0)
        if timestamp:
          yield MsieWebCacheContainerEventObject(
              timestamp, eventdata.EventTimestamp.EXPIRATION_TIME,
              record_values)

        timestamp = record_values.get(u'ModifiedTime', 0)
        if timestamp:
          yield MsieWebCacheContainerEventObject(
              timestamp, eventdata.EventTimestamp.MODIFICATION_TIME,
              record_values)

        timestamp = record_values.get(u'AccessedTime', 0)
        if timestamp:
          yield MsieWebCacheContainerEventObject(
              timestamp, eventdata.EventTimestamp.ACCESS_TIME, record_values)

        timestamp = record_values.get(u'PostCheckTime', 0)
        if timestamp:
          yield MsieWebCacheContainerEventObject(
              timestamp, u'Post check time', record_values)

  def ParseContainersTable(
      self, unused_parser_context, database=None, table=None, **unused_kwargs):
    """Parses the Containers table.

    Args:
      parser_context: A parser context object (instance of ParserContext).
      database: Optional database object (instance of pyesedb.file).
                The default is None.
      table: Optional table object (instance of pyesedb.table).
             The default is None.

    Yields:
      An event object (instance of EventObject).
    """
    if database is None:
      logging.warning(u'[{0:s}] invalid database'.format(self.NAME))
      return

    if table is None:
      logging.warning(u'[{0:s}] invalid Containers table'.format(self.NAME))
      return

    for esedb_record in table.records:
      record_values = self._GetRecordValues(table.name, esedb_record)

      timestamp = record_values.get(u'LastScavengeTime', 0)
      if timestamp:
        yield MsieWebCacheContainersEventObject(
            timestamp, u'Last Scavenge Time', record_values)

      timestamp = record_values.get(u'LastAccessTime', 0)
      if timestamp:
        yield MsieWebCacheContainersEventObject(
            timestamp, eventdata.EventTimestamp.ACCESS_TIME, record_values)

      container_identifier = record_values.get(u'ContainerId', None)
      container_name = record_values.get(u'Name', None)

      if not container_identifier or not container_name:
        continue

      table_name = u'Container_{0:d}'.format(container_identifier)
      esedb_table = database.get_table_by_name(table_name)
      if not esedb_table:
        logging.warning(
            u'[{0:s}] missing table: {1:s}'.format(self.NAME, table_name))
        continue

      for event_object in self._ParseContainerTable(
          esedb_table, container_name):
        yield event_object

  def ParseLeakFilesTable(
      self, unused_parser_context, database=None, table=None, **unused_kwargs):
    """Parses the LeakFiles table.

    Args:
      parser_context: A parser context object (instance of ParserContext).
      database: Optional database object (instance of pyesedb.file).
                The default is None.
      table: Optional table object (instance of pyesedb.table).
             The default is None.

    Yields:
      An event object (instance of EventObject).
    """
    if database is None:
      logging.warning(u'[{0:s}] invalid database'.format(self.NAME))
      return

    if table is None:
      logging.warning(u'[{0:s}] invalid LeakFiles table'.format(self.NAME))
      return

    for esedb_record in table.records:
      record_values = self._GetRecordValues(table.name, esedb_record)

      timestamp = record_values.get(u'CreationTime', 0)
      if timestamp:
        yield MsieWebCacheLeakFilesEventObject(
            timestamp, eventdata.EventTimestamp.CREATION_TIME, record_values)

  def ParsePartitionsTable(
      self, unused_parser_context, database=None, table=None, **unused_kwargs):
    """Parses the Partitions table.

    Args:
      parser_context: A parser context object (instance of ParserContext).
      database: Optional database object (instance of pyesedb.file).
                The default is None.
      table: Optional table object (instance of pyesedb.table).
             The default is None.

    Yields:
      An event object (instance of EventObject).
    """
    if database is None:
      logging.warning(u'[{0:s}] invalid database'.format(self.NAME))
      return

    if table is None:
      logging.warning(u'[{0:s}] invalid Partitions table'.format(self.NAME))
      return

    for esedb_record in table.records:
      record_values = self._GetRecordValues(table.name, esedb_record)

      timestamp = record_values.get(u'LastScavengeTime', 0)
      if timestamp:
        yield MsieWebCachePartitionsEventObject(
            timestamp, u'Last Scavenge Time', record_values)
