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
    container_identifier (str): container identifier.
    directory (str): name of the cache directory.
    name (str): name of the cache container.
    set_identifier (str): set identifier.
  """

  DATA_TYPE = u'msie:webcache:containers'

  # TODO: replace record values by explicit arguments.
  def __init__(self, filetime, timestamp_description, record_values):
    """Initializes the event.

    Args:
      filetime (int): FILETIME timestamp value.
      timestamp_description (str): description of the usage of the timestamp
          value.
      record_values (dict[str,object]): record values.
    """
    super(MsieWebCacheContainersEventObject, self).__init__(
        filetime, timestamp_description)
    self.container_identifier = record_values.get(u'ContainerId', 0)
    self.directory = record_values.get(u'Directory', u'')
    self.name = record_values.get(u'Name', u'')
    self.set_identifier = record_values.get(u'SetId', 0)


class MsieWebCacheContainerEventObject(time_events.FiletimeEvent):
  """Convenience class for a MSIE WebCache Container table event."""

  DATA_TYPE = u'msie:webcache:container'

  # TODO: replace record values by explicit arguments.
  def __init__(self, filetime, timestamp_description, record_values):
    """Initializes the event.

    Args:
      filetime (int): FILETIME timestamp value.
      timestamp_description (str): description of the usage of the timestamp
          value.
      record_values (dict[str,object]): record values.
    """
    super(MsieWebCacheContainerEventObject, self).__init__(
        filetime, timestamp_description)

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

    self.cached_filename = record_values.get(u'Filename', u'')
    self.file_extension = record_values.get(u'FileExtension', u'')
    self.cached_file_size = record_values.get(u'FileSize', 0)

    # Ignore non-Unicode request headers values.
    request_headers = record_values.get(u'RequestHeaders', u'')
    if isinstance(request_headers, py2to3.UNICODE_TYPE) and request_headers:
      self.request_headers = request_headers

    # Ignore non-Unicode response headers values.
    response_headers = record_values.get(u'ResponseHeaders', u'')
    if isinstance(response_headers, py2to3.UNICODE_TYPE) and response_headers:
      self.response_headers = response_headers


class MsieWebCacheLeakFilesEventObject(time_events.FiletimeEvent):
  """Convenience class for a MSIE WebCache LeakFiles table event."""

  DATA_TYPE = u'msie:webcache:leak_file'

  # TODO: replace record values by explicit arguments.
  def __init__(self, filetime, timestamp_description, record_values):
    """Initializes the event.

    Args:
      filetime (int): FILETIME timestamp value.
      timestamp_description (str): description of the usage of the timestamp
          value.
      record_values (dict[str,object]): record values.
    """
    super(MsieWebCacheLeakFilesEventObject, self).__init__(
        filetime, timestamp_description)

    self.leak_identifier = record_values.get(u'LeakId', 0)
    self.cached_filename = record_values.get(u'Filename', u'')


class MsieWebCachePartitionsEventObject(time_events.FiletimeEvent):
  """Convenience class for a MSIE WebCache Partitions table event."""

  DATA_TYPE = u'msie:webcache:partitions'

  # TODO: replace record values by explicit arguments.
  def __init__(self, filetime, timestamp_description, record_values):
    """Initializes the event.

    Args:
      filetime (int): FILETIME timestamp value.
      timestamp_description (str): description of the usage of the timestamp
          value.
      record_values (dict[str,object]): record values.
    """
    super(MsieWebCachePartitionsEventObject, self).__init__(
        filetime, timestamp_description)

    self.partition_identifier = record_values.get(u'PartitionId', 0)
    self.partition_type = record_values.get(u'PartitionType', 0)
    self.directory = record_values.get(u'Directory', u'')
    self.table_identifier = record_values.get(u'TableId', 0)


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

      if (container_name in (
          u'Content', u'Cookies', u'History', u'iedownload') or
          container_name.startswith(u'MSHist')):
        timestamp = record_values.get(u'SyncTime', 0)
        if timestamp:
          event_object = MsieWebCacheContainerEventObject(
              timestamp, u'Synchronization time', record_values)
          parser_mediator.ProduceEvent(event_object)

        timestamp = record_values.get(u'CreationTime', 0)
        if timestamp:
          event_object = MsieWebCacheContainerEventObject(
              timestamp, eventdata.EventTimestamp.CREATION_TIME, record_values)
          parser_mediator.ProduceEvent(event_object)

        timestamp = record_values.get(u'ExpiryTime', 0)
        if timestamp:
          event_object = MsieWebCacheContainerEventObject(
              timestamp, eventdata.EventTimestamp.EXPIRATION_TIME,
              record_values)
          parser_mediator.ProduceEvent(event_object)

        timestamp = record_values.get(u'ModifiedTime', 0)
        if timestamp:
          event_object = MsieWebCacheContainerEventObject(
              timestamp, eventdata.EventTimestamp.MODIFICATION_TIME,
              record_values)
          parser_mediator.ProduceEvent(event_object)

        timestamp = record_values.get(u'AccessedTime', 0)
        if timestamp:
          event_object = MsieWebCacheContainerEventObject(
              timestamp, eventdata.EventTimestamp.ACCESS_TIME, record_values)
          parser_mediator.ProduceEvent(event_object)

        timestamp = record_values.get(u'PostCheckTime', 0)
        if timestamp:
          event_object = MsieWebCacheContainerEventObject(
              timestamp, u'Post check time', record_values)
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

      timestamp = record_values.get(u'LastScavengeTime', 0)
      if timestamp:
        event_object = MsieWebCacheContainersEventObject(
            timestamp, u'Last Scavenge Time', record_values)
        parser_mediator.ProduceEvent(event_object)

      timestamp = record_values.get(u'LastAccessTime', 0)
      if timestamp:
        event_object = MsieWebCacheContainersEventObject(
            timestamp, eventdata.EventTimestamp.ACCESS_TIME, record_values)
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

      timestamp = record_values.get(u'CreationTime', 0)
      if timestamp:
        event_object = MsieWebCacheLeakFilesEventObject(
            timestamp, eventdata.EventTimestamp.CREATION_TIME, record_values)
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

      timestamp = record_values.get(u'LastScavengeTime', 0)
      if timestamp:
        event_object = MsieWebCachePartitionsEventObject(
            timestamp, u'Last Scavenge Time', record_values)
        parser_mediator.ProduceEvent(event_object)


esedb.ESEDBParser.RegisterPlugin(MsieWebCacheESEDBPlugin)
