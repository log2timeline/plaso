# -*- coding: utf-8 -*-
"""Parser for the Microsoft Internet Explorer WebCache ESE database.

The WebCache database (WebCacheV01.dat or WebCacheV24.dat) are used by MSIE
as of version 10.
"""

import logging

from dfdatetime import filetime as dfdatetime_filetime

from plaso.containers import events
from plaso.containers import time_events
from plaso.lib import definitions
from plaso.lib import py2to3
from plaso.parsers import esedb
from plaso.parsers.esedb_plugins import interface


class MsieWebCacheContainersEventData(events.EventData):
  """MSIE WebCache Containers table event data.

  Attributes:
    container_identifier (int): container identifier.
    directory (str): name of the cache directory.
    name (str): name of the cache container.
    set_identifier (int): set identifier.
  """

  DATA_TYPE = u'msie:webcache:containers'

  def __init__(self):
    """Initializes event data."""
    super(MsieWebCacheContainersEventData, self).__init__(
        data_type=self.DATA_TYPE)
    self.container_identifier = None
    self.directory = None
    self.name = None
    self.set_identifier = None


class MsieWebCacheContainerEventData(events.EventData):
  """MSIE WebCache Container table event data.

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

  def __init__(self):
    """Initializes event data."""
    super(MsieWebCacheContainerEventData, self).__init__(
        data_type=self.DATA_TYPE)
    self.access_count = None
    self.cached_filename = None
    self.cached_file_size = None
    self.cache_identifier = None
    self.container_identifier = None
    self.entry_identifier = None
    self.file_extension = None
    self.redirect_url = None
    self.request_headers = None
    self.response_headers = None
    self.sync_count = None
    self.url = None


class MsieWebCacheLeakFilesEventData(events.EventData):
  """MSIE WebCache LeakFiles event data.

  Attributes:
    cached_filename (str): name of the cached file.
    leak_identifier (int): leak identifier.
  """

  DATA_TYPE = u'msie:webcache:leak_file'

  def __init__(self):
    """Initializes event data."""
    super(MsieWebCacheLeakFilesEventData, self).__init__(
        data_type=self.DATA_TYPE)
    self.cached_filename = None
    self.leak_identifier = None


class MsieWebCachePartitionsEventData(events.EventData):
  """MSIE WebCache Partitions table event data.

  Attributes:
    directory (str): directory.
    partition_identifier (int): partition identifier.
    partition_type (int): partition type.
    table_identifier (int): table identifier.
  """

  DATA_TYPE = u'msie:webcache:partitions'

  def __init__(self):
    """Initializes event data."""
    super(MsieWebCachePartitionsEventData, self).__init__(
        data_type=self.DATA_TYPE)
    self.directory = None
    self.partition_identifier = None
    self.partition_type = None
    self.table_identifier = None


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
      parser_mediator (ParserMediator): mediates interactions between parsers
          and other components, such as storage and dfvfs.
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

        event_data = MsieWebCacheContainerEventData()
        event_data.access_count = access_count
        event_data.cached_filename = cached_filename
        event_data.cached_file_size = cached_file_size
        event_data.cache_identifier = cache_identifier
        event_data.container_identifier = container_identifier
        event_data.entry_identifier = entry_identifier
        event_data.file_extension = file_extension
        event_data.redirect_url = redirect_url
        event_data.request_headers = request_headers
        event_data.response_headers = response_headers
        event_data.sync_count = sync_count
        event_data.url = url

        timestamp = record_values.get(u'SyncTime', None)
        if timestamp:
          date_time = dfdatetime_filetime.Filetime(timestamp=timestamp)
          event = time_events.DateTimeValuesEvent(
              date_time, u'Synchronization time')
          parser_mediator.ProduceEventWithEventData(event, event_data)

        timestamp = record_values.get(u'CreationTime', None)
        if timestamp:
          date_time = dfdatetime_filetime.Filetime(timestamp=timestamp)
          event = time_events.DateTimeValuesEvent(
              date_time, definitions.TIME_DESCRIPTION_CREATION)
          parser_mediator.ProduceEventWithEventData(event, event_data)

        timestamp = record_values.get(u'ExpiryTime', None)
        if timestamp:
          date_time = dfdatetime_filetime.Filetime(timestamp=timestamp)
          event = time_events.DateTimeValuesEvent(
              date_time, definitions.TIME_DESCRIPTION_EXPIRATION)
          parser_mediator.ProduceEventWithEventData(event, event_data)

        timestamp = record_values.get(u'ModifiedTime', None)
        if timestamp:
          date_time = dfdatetime_filetime.Filetime(timestamp=timestamp)
          event = time_events.DateTimeValuesEvent(
              date_time, definitions.TIME_DESCRIPTION_MODIFICATION)
          parser_mediator.ProduceEventWithEventData(event, event_data)

        timestamp = record_values.get(u'AccessedTime', None)
        if timestamp:
          date_time = dfdatetime_filetime.Filetime(timestamp=timestamp)
          event = time_events.DateTimeValuesEvent(
              date_time, definitions.TIME_DESCRIPTION_LAST_ACCESS)
          parser_mediator.ProduceEventWithEventData(event, event_data)

        timestamp = record_values.get(u'PostCheckTime', None)
        if timestamp:
          date_time = dfdatetime_filetime.Filetime(timestamp=timestamp)
          event = time_events.DateTimeValuesEvent(
              date_time, u'Post check time')
          parser_mediator.ProduceEventWithEventData(event, event_data)

  def ParseContainersTable(
      self, parser_mediator, database=None, table=None, **unused_kwargs):
    """Parses the Containers table.

    Args:
      parser_mediator (ParserMediator): mediates interactions between parsers
          and other components, such as storage and dfvfs.
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

      event_data = MsieWebCacheContainersEventData()
      event_data.container_identifier = record_values.get(u'ContainerId', None)
      event_data.directory = record_values.get(u'Directory', None)
      event_data.name = record_values.get(u'Name', None)
      event_data.set_identifier = record_values.get(u'SetId', None)

      timestamp = record_values.get(u'LastScavengeTime', None)
      if timestamp:
        date_time = dfdatetime_filetime.Filetime(timestamp=timestamp)
        event = time_events.DateTimeValuesEvent(
            date_time, u'Last Scavenge Time')
        parser_mediator.ProduceEventWithEventData(event, event_data)

      timestamp = record_values.get(u'LastAccessTime', None)
      if timestamp:
        date_time = dfdatetime_filetime.Filetime(timestamp=timestamp)
        event = time_events.DateTimeValuesEvent(
            date_time, definitions.TIME_DESCRIPTION_LAST_ACCESS)
        parser_mediator.ProduceEventWithEventData(event, event_data)

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
      parser_mediator (ParserMediator): mediates interactions between parsers
          and other components, such as storage and dfvfs.
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

      event_data = MsieWebCacheLeakFilesEventData()
      event_data.cached_filename = record_values.get(u'Filename', None)
      event_data.leak_identifier = record_values.get(u'LeakId', None)

      timestamp = record_values.get(u'CreationTime', None)
      if timestamp:
        date_time = dfdatetime_filetime.Filetime(timestamp=timestamp)
        event = time_events.DateTimeValuesEvent(
            date_time, definitions.TIME_DESCRIPTION_CREATION)
        parser_mediator.ProduceEventWithEventData(event, event_data)

  def ParsePartitionsTable(
      self, parser_mediator, database=None, table=None, **unused_kwargs):
    """Parses the Partitions table.

    Args:
      parser_mediator (ParserMediator): mediates interactions between parsers
          and other components, such as storage and dfvfs.
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

      event_data = MsieWebCachePartitionsEventData()
      event_data.directory = record_values.get(u'Directory', None)
      event_data.partition_identifier = record_values.get(u'PartitionId', None)
      event_data.partition_type = record_values.get(u'PartitionType', None)
      event_data.table_identifier = record_values.get(u'TableId', None)

      timestamp = record_values.get(u'LastScavengeTime', None)
      if timestamp:
        date_time = dfdatetime_filetime.Filetime(timestamp=timestamp)
        event = time_events.DateTimeValuesEvent(
            date_time, u'Last Scavenge Time')
        parser_mediator.ProduceEventWithEventData(event, event_data)


esedb.ESEDBParser.RegisterPlugin(MsieWebCacheESEDBPlugin)
