# -*- coding: utf-8 -*-
"""Parser for the Microsoft Internet Explorer WebCache ESE database.

The WebCache database (WebCacheV01.dat or WebCacheV24.dat) are used by MSIE
as of version 10.
"""

import logging

from plaso.containers import time_events
from plaso.lib import eventdata
from plaso.lib import py2to3
from plaso.parsers import esedb
from plaso.parsers.esedb_plugins import interface


class MsieWebCacheContainersEventObject(time_events.FiletimeEvent):
  """Convenience class for a MSIE WebCache Containers table event.

  Attributes:
    container_identifier (int): container identifier.
    directory (str): name of the cache directory.
    name (str): name of the cache container.
    set_identifier (int): set identifier.
  """

  DATA_TYPE = u'msie:webcache:containers'

  def __init__(
      self, filetime, timestamp_description, container_identifier, directory,
      name, set_identifier):
    """Initializes an event.

    Args:
      filetime (int): FILETIME timestamp value.
      timestamp_description (str): description of the meaning of the timestamp
          value.
      container_identifier (int): container identifier.
      directory (str): name of the cache directory.
      name (str): name of the cache container.
      set_identifier (int): set identifier.
    """
    super(MsieWebCacheContainersEventObject, self).__init__(
        filetime, timestamp_description)
    self.container_identifier = container_identifier
    self.directory = directory
    self.name = name
    self.set_identifier = set_identifier


class MsieWebCacheContainerEventObject(time_events.FiletimeEvent):
  """Convenience class for a MSIE WebCache Container table event.

  Attributes:
    access_count (int): access count.
    cached_filename (str): name of the cached file.
    cached_file_size (int): size of the cached file.
    cache_identifier (int): cache identifier.
    container_identifier (int): container identifier.
    entry_identifier (int): entry identifier.
    file_extension (str): file extension.
    redirect_url (str): URL from which the request was redirected.
    request_headers (str): request headers.
    response_headers (str): response headers.
    sync_count (int): sync count.
    url (str): URL.
  """

  DATA_TYPE = u'msie:webcache:container'

  def __init__(
      self, filetime, timestamp_description, cache_identifier,
      container_identifier, entry_identifier, access_count, sync_count,
      cached_filename, file_extension, cached_file_size, url, redirect_url,
      request_headers, response_headers):
    """Initializes an event.

    Args:
      filetime (int): FILETIME timestamp value.
      timestamp_description (str): description of the meaning of the timestamp
          value.
      cache_identifier (int): cache identifier.
      container_identifier (int): container identifier.
      entry_identifier (int): entry identifier.
      access_count (int): access count.
      sync_count (int): sync count.
      cached_filename (str): name of the cached file.
      file_extension (str): file extension.
      cached_file_size (int): size of the cached file.
      url (str): URL.
      redirect_url (str): URL from which the request was redirected.
      request_headers (str): request headers.
      response_headers (str): response headers.
    """
    super(MsieWebCacheContainerEventObject, self).__init__(
        filetime, timestamp_description)
    self.access_count = access_count
    self.cached_filename = cached_filename
    self.cached_file_size = cached_file_size
    self.cache_identifier = cache_identifier
    self.container_identifier = container_identifier
    self.entry_identifier = entry_identifier
    self.file_extension = file_extension
    self.redirect_url = redirect_url
    self.request_headers = request_headers
    self.response_headers = response_headers
    self.sync_count = sync_count
    self.url = url


class MsieWebCacheLeakFilesEventObject(time_events.FiletimeEvent):
  """Convenience class for a MSIE WebCache LeakFiles table event.

  Attributes:
    cached_filename (str): name of the cached file.
    leak_identifier (int): leak identifier.
  """

  DATA_TYPE = u'msie:webcache:leak_file'

  def __init__(
      self, filetime, timestamp_description, leak_identifier, cached_filename):
    """Initializes an event.

    Args:
      filetime (int): FILETIME timestamp value.
      timestamp_description (str): description of the meaning of the timestamp
          value.
      leak_identifier (int): leak identifier.
      cached_filename (str): name of the cached file.
    """
    super(MsieWebCacheLeakFilesEventObject, self).__init__(
        filetime, timestamp_description)
    self.cached_filename = cached_filename
    self.leak_identifier = leak_identifier


class MsieWebCachePartitionsEventObject(time_events.FiletimeEvent):
  """Convenience class for a MSIE WebCache Partitions table event.

  Attributes:
    directory (str): directory.
    partition_identifier (int): partition identifier.
    partition_type (int): partition type.
    table_identifier (int): table identifier.
  """

  DATA_TYPE = u'msie:webcache:partitions'

  def __init__(
      self, filetime, timestamp_description, directory, partition_identifier,
      partition_type, table_identifier):
    """Initializes an event.

    Args:
      filetime (int): FILETIME timestamp value.
      timestamp_description (str): description of the meaning of the timestamp
          value.
      directory (str): directory.
      partition_identifier (int): partition identifier.
      partition_type (int): partition type.
      table_identifier (int): table identifier.
    """
    super(MsieWebCachePartitionsEventObject, self).__init__(
        filetime, timestamp_description)
    self.directory = directory
    self.partition_identifier = partition_identifier
    self.partition_type = partition_type
    self.table_identifier = table_identifier


class MsieWebCacheESEDBPlugin(interface.ESEDBPlugin):
  """Parses a MSIE WebCache ESE database file."""

  NAME = u'msie_webcache'
  DESCRIPTION = u'Parser for MSIE WebCache ESE database files.'

  # TODO: add support for AppCache_#, AppCacheEntry_#, DependencyEntry_#

  REQUIRED_TABLES = {
      u'Containers': u'ParseContainersTable',
      u'LeakFiles': u'ParseLeakFilesTable',
      u'Partitions': u'ParsePartitionsTable'}

  _CONTAINER_TABLE_VALUE_MAPPINGS = {
      u'RequestHeaders': u'_ConvertValueBinaryDataToStringAscii',
      u'ResponseHeaders': u'_ConvertValueBinaryDataToStringAscii'}

  _SUPPORTED_CONTAINER_NAMES = frozenset([
      u'Content', u'Cookies', u'History', u'iedownload'])

  def _ParseContainerTable(self, parser_mediator, table, container_name):
    """Parses a Container_# table.

    Args:
      parser_mediator (ParserMediator): parser mediator.
      table (pyesedb.table): table.
      container_name (str): container name, which indicates the table type.
    """
    if table is None:
      logging.warning(u'[{0:s}] invalid Container_# table'.format(self.NAME))
      return

    for record_index, esedb_record in enumerate(table.records):
      if parser_mediator.abort:
        break

      # TODO: add support for:
      # wpnidm, iecompat, iecompatua, DNTException, DOMStore
      if container_name == u'Content':
        value_mappings = self._CONTAINER_TABLE_VALUE_MAPPINGS
      else:
        value_mappings = None

      try:
        record_values = self._GetRecordValues(
            parser_mediator, table.name, esedb_record,
            value_mappings=value_mappings)

      except UnicodeDecodeError:
        parser_mediator.ProduceExtractionError((
            u'Unable to retrieve record values from record: {0:d} '
            u'in table: {1:s}').format(record_index, table.name))
        continue

      if (container_name in self._SUPPORTED_CONTAINER_NAMES or
          container_name.startswith(u'MSHist')):
        access_count = record_values.get(u'AccessCount', None)
        cached_filename = record_values.get(u'Filename', None)
        cached_file_size = record_values.get(u'FileSize', None)
        cache_identifier = record_values.get(u'CacheId', None)
        container_identifier = record_values.get(u'ContainerId', None)
        entry_identifier = record_values.get(u'EntryId', None)
        file_extension = record_values.get(u'FileExtension', None)
        redirect_url = record_values.get(u'RedirectUrl', None)
        sync_count = record_values.get(u'SyncCount', None)

        url = record_values.get(u'Url', u'')
        # Ignore an URL that start with a binary value.
        if ord(url[0]) < 0x20 or ord(url[0]) == 0x7f:
          url = None

        request_headers = record_values.get(u'RequestHeaders', None)
        # Ignore non-Unicode request headers values.
        if not isinstance(request_headers, py2to3.UNICODE_TYPE):
          request_headers = None

        response_headers = record_values.get(u'ResponseHeaders', None)
        # Ignore non-Unicode response headers values.
        if not isinstance(response_headers, py2to3.UNICODE_TYPE):
          response_headers = None

        timestamp = record_values.get(u'SyncTime', None)
        if timestamp:
          event_object = MsieWebCacheContainerEventObject(
              timestamp, u'Synchronization time', cache_identifier,
              container_identifier, entry_identifier, access_count, sync_count,
              cached_filename, file_extension, cached_file_size, url,
              redirect_url, request_headers, response_headers)
          parser_mediator.ProduceEvent(event_object)

        timestamp = record_values.get(u'CreationTime', None)
        if timestamp:
          event_object = MsieWebCacheContainerEventObject(
              timestamp, eventdata.EventTimestamp.CREATION_TIME,
              cache_identifier, container_identifier, entry_identifier,
              access_count, sync_count, cached_filename, file_extension,
              cached_file_size, url, redirect_url, request_headers,
              response_headers)
          parser_mediator.ProduceEvent(event_object)

        timestamp = record_values.get(u'ExpiryTime', None)
        if timestamp:
          event_object = MsieWebCacheContainerEventObject(
              timestamp, eventdata.EventTimestamp.EXPIRATION_TIME,
              cache_identifier, container_identifier, entry_identifier,
              access_count, sync_count, cached_filename, file_extension,
              cached_file_size, url, redirect_url, request_headers,
              response_headers)
          parser_mediator.ProduceEvent(event_object)

        timestamp = record_values.get(u'ModifiedTime', None)
        if timestamp:
          event_object = MsieWebCacheContainerEventObject(
              timestamp, eventdata.EventTimestamp.MODIFICATION_TIME,
              cache_identifier, container_identifier, entry_identifier,
              access_count, sync_count, cached_filename, file_extension,
              cached_file_size, url, redirect_url, request_headers,
              response_headers)
          parser_mediator.ProduceEvent(event_object)

        timestamp = record_values.get(u'AccessedTime', None)
        if timestamp:
          event_object = MsieWebCacheContainerEventObject(
              timestamp, eventdata.EventTimestamp.ACCESS_TIME,
              cache_identifier, container_identifier, entry_identifier,
              access_count, sync_count, cached_filename, file_extension,
              cached_file_size, url,
              redirect_url, request_headers, response_headers)
          parser_mediator.ProduceEvent(event_object)

        timestamp = record_values.get(u'PostCheckTime', None)
        if timestamp:
          event_object = MsieWebCacheContainerEventObject(
              timestamp, u'Post check time', cache_identifier,
              container_identifier, entry_identifier, access_count, sync_count,
              cached_filename, file_extension, cached_file_size, url,
              redirect_url, request_headers, response_headers)
          parser_mediator.ProduceEvent(event_object)

  def ParseContainersTable(
      self, parser_mediator, database=None, table=None, **unused_kwargs):
    """Parses the Containers table.

    Args:
      parser_mediator (ParserMediator): parser mediator.
      database (Optional[pyesedb.file]): ESE database.
      table (Optional[pyesedb.table]): table.
    """
    if database is None:
      logging.warning(u'[{0:s}] invalid database'.format(self.NAME))
      return

    if table is None:
      logging.warning(u'[{0:s}] invalid Containers table'.format(self.NAME))
      return

    for esedb_record in table.records:
      if parser_mediator.abort:
        break

      record_values = self._GetRecordValues(
          parser_mediator, table.name, esedb_record)

      container_identifier = record_values.get(u'ContainerId', None)
      directory = record_values.get(u'Directory', None)
      name = record_values.get(u'Name', None)
      set_identifier = record_values.get(u'SetId', None)

      timestamp = record_values.get(u'LastScavengeTime', None)
      if timestamp:
        event_object = MsieWebCacheContainersEventObject(
            timestamp, u'Last Scavenge Time', container_identifier, directory,
            name, set_identifier)
        parser_mediator.ProduceEvent(event_object)

      timestamp = record_values.get(u'LastAccessTime', None)
      if timestamp:
        event_object = MsieWebCacheContainersEventObject(
            timestamp, eventdata.EventTimestamp.ACCESS_TIME,
            container_identifier, directory, name, set_identifier)
        parser_mediator.ProduceEvent(event_object)

      container_identifier = record_values.get(u'ContainerId', None)
      container_name = record_values.get(u'Name', None)

      if not container_identifier or not container_name:
        continue

      table_name = u'Container_{0:d}'.format(container_identifier)
      esedb_table = database.get_table_by_name(table_name)
      if not esedb_table:
        parser_mediator.ProduceExtractionError(
            u'Missing table: {0:s}'.format(table_name))
        continue

      self._ParseContainerTable(parser_mediator, esedb_table, container_name)

  def ParseLeakFilesTable(
      self, parser_mediator, database=None, table=None, **unused_kwargs):
    """Parses the LeakFiles table.

    Args:
      parser_mediator (ParserMediator): parser mediator.
      database (Optional[pyesedb.file]): ESE database.
      table (Optional[pyesedb.table]): table.
    """
    if database is None:
      logging.warning(u'[{0:s}] invalid database'.format(self.NAME))
      return

    if table is None:
      logging.warning(u'[{0:s}] invalid LeakFiles table'.format(self.NAME))
      return

    for esedb_record in table.records:
      if parser_mediator.abort:
        break

      record_values = self._GetRecordValues(
          parser_mediator, table.name, esedb_record)

      timestamp = record_values.get(u'CreationTime', None)
      if timestamp:
        cached_filename = record_values.get(u'Filename', None)
        leak_identifier = record_values.get(u'LeakId', None)

        event_object = MsieWebCacheLeakFilesEventObject(
            timestamp, eventdata.EventTimestamp.CREATION_TIME, leak_identifier,
            cached_filename)
        parser_mediator.ProduceEvent(event_object)

  def ParsePartitionsTable(
      self, parser_mediator, database=None, table=None, **unused_kwargs):
    """Parses the Partitions table.

    Args:
      parser_mediator (ParserMediator): parser mediator.
      database (Optional[pyesedb.file]): ESE database.
      table (Optional[pyesedb.table]): table.
    """
    if database is None:
      logging.warning(u'[{0:s}] invalid database'.format(self.NAME))
      return

    if table is None:
      logging.warning(u'[{0:s}] invalid Partitions table'.format(self.NAME))
      return

    for esedb_record in table.records:
      if parser_mediator.abort:
        break

      record_values = self._GetRecordValues(
          parser_mediator, table.name, esedb_record)

      timestamp = record_values.get(u'LastScavengeTime', None)
      if timestamp:
        directory = record_values.get(u'Directory', None)
        partition_identifier = record_values.get(u'PartitionId', None)
        partition_type = record_values.get(u'PartitionType', None)
        table_identifier = record_values.get(u'TableId', None)

        event_object = MsieWebCachePartitionsEventObject(
            timestamp, u'Last Scavenge Time', directory, partition_identifier,
            partition_type, table_identifier)
        parser_mediator.ProduceEvent(event_object)


esedb.ESEDBParser.RegisterPlugin(MsieWebCacheESEDBPlugin)
