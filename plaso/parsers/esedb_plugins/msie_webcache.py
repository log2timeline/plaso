# -*- coding: utf-8 -*-
"""Parser for the Microsoft Internet Explorer WebCache ESE database.

The WebCache database (WebCacheV01.dat or WebCacheV24.dat) are used by MSIE
as of version 10.
"""

from __future__ import unicode_literals

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

  DATA_TYPE = 'msie:webcache:containers'

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

  DATA_TYPE = 'msie:webcache:container'

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

  DATA_TYPE = 'msie:webcache:leak_file'

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

  DATA_TYPE = 'msie:webcache:partitions'

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

  NAME = 'msie_webcache'
  DESCRIPTION = 'Parser for MSIE WebCache ESE database files.'

  # TODO: add support for AppCache_#, AppCacheEntry_#, DependencyEntry_#

  REQUIRED_TABLES = {
      'Containers': 'ParseContainersTable',
      'LeakFiles': 'ParseLeakFilesTable'}

  OPTIONAL_TABLES = {
      'Partitions': 'ParsePartitionsTable',
      'PartitionsEx': 'ParsePartitionsTable'}

  _CONTAINER_TABLE_VALUE_MAPPINGS = {
      'RequestHeaders': '_ConvertHeadersValues',
      'ResponseHeaders': '_ConvertHeadersValues'}

  _SUPPORTED_CONTAINER_NAMES = frozenset([
      'Content', 'Cookies', 'History', 'iedownload'])

  _IGNORED_CONTAINER_NAMES = frozenset([
      'MicrosoftEdge_DNTException', 'MicrosoftEdge_EmieSiteList',
      'MicrosoftEdge_EmieUserList'])

  def _ConvertHeadersValues(self, value):
    """Converts a headers value into a string.

    Args:
      value (bytes): binary data value containing the headers as an ASCII string
          or None.

    Returns:
      str: string representation of headers value or None.
    """
    if value:
      value = value.decode('ascii')
      header_values = [value.strip() for value in value.split('\r\n') if value]
      return '[{0:s}]'.format('; '.join(header_values))

    return None

  def _ParseContainerTable(self, parser_mediator, table, container_name):
    """Parses a Container_# table.

    Args:
      parser_mediator (ParserMediator): mediates interactions between parsers
          and other components, such as storage and dfvfs.
      table (pyesedb.table): table.
      container_name (str): container name, which indicates the table type.

    Raises:
      ValueError: if the table value is missing.
    """
    if table is None:
      raise ValueError('Missing table value.')

    for record_index, esedb_record in enumerate(table.records):
      if parser_mediator.abort:
        break

      # TODO: add support for:
      # wpnidm, iecompat, iecompatua, DNTException, DOMStore
      if container_name == 'Content':
        value_mappings = self._CONTAINER_TABLE_VALUE_MAPPINGS
      else:
        value_mappings = None

      try:
        record_values = self._GetRecordValues(
            parser_mediator, table.name, esedb_record,
            value_mappings=value_mappings)

      except UnicodeDecodeError:
        parser_mediator.ProduceExtractionWarning((
            'Unable to retrieve record values from record: {0:d} '
            'in table: {1:s}').format(record_index, table.name))
        continue

      if (container_name in self._SUPPORTED_CONTAINER_NAMES or
          container_name.startswith('MSHist')):
        access_count = record_values.get('AccessCount', None)
        cached_filename = record_values.get('Filename', None)
        cached_file_size = record_values.get('FileSize', None)
        cache_identifier = record_values.get('CacheId', None)
        container_identifier = record_values.get('ContainerId', None)
        entry_identifier = record_values.get('EntryId', None)
        file_extension = record_values.get('FileExtension', None)
        redirect_url = record_values.get('RedirectUrl', None)
        sync_count = record_values.get('SyncCount', None)

        url = record_values.get('Url', '')
        # Ignore an URL that start with a binary value.
        if ord(url[0]) < 0x20 or ord(url[0]) == 0x7f:
          url = None

        request_headers = record_values.get('RequestHeaders', None)
        # Ignore non-Unicode request headers values.
        if not isinstance(request_headers, py2to3.UNICODE_TYPE):
          request_headers = None

        response_headers = record_values.get('ResponseHeaders', None)
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

        timestamp = record_values.get('SyncTime', None)
        if timestamp:
          date_time = dfdatetime_filetime.Filetime(timestamp=timestamp)
          event = time_events.DateTimeValuesEvent(
              date_time, 'Synchronization time')
          parser_mediator.ProduceEventWithEventData(event, event_data)

        timestamp = record_values.get('CreationTime', None)
        if timestamp:
          date_time = dfdatetime_filetime.Filetime(timestamp=timestamp)
          event = time_events.DateTimeValuesEvent(
              date_time, definitions.TIME_DESCRIPTION_CREATION)
          parser_mediator.ProduceEventWithEventData(event, event_data)

        timestamp = record_values.get('ExpiryTime', None)
        if timestamp:
          date_time = dfdatetime_filetime.Filetime(timestamp=timestamp)
          event = time_events.DateTimeValuesEvent(
              date_time, definitions.TIME_DESCRIPTION_EXPIRATION)
          parser_mediator.ProduceEventWithEventData(event, event_data)

        timestamp = record_values.get('ModifiedTime', None)
        if timestamp:
          date_time = dfdatetime_filetime.Filetime(timestamp=timestamp)
          event = time_events.DateTimeValuesEvent(
              date_time, definitions.TIME_DESCRIPTION_MODIFICATION)
          parser_mediator.ProduceEventWithEventData(event, event_data)

        timestamp = record_values.get('AccessedTime', None)
        if timestamp:
          date_time = dfdatetime_filetime.Filetime(timestamp=timestamp)
          event = time_events.DateTimeValuesEvent(
              date_time, definitions.TIME_DESCRIPTION_LAST_ACCESS)
          parser_mediator.ProduceEventWithEventData(event, event_data)

        timestamp = record_values.get('PostCheckTime', None)
        if timestamp:
          date_time = dfdatetime_filetime.Filetime(timestamp=timestamp)
          event = time_events.DateTimeValuesEvent(
              date_time, 'Post check time')
          parser_mediator.ProduceEventWithEventData(event, event_data)

  def ParseContainersTable(
      self, parser_mediator, database=None, table=None, **unused_kwargs):
    """Parses a Containers table.

    Args:
      parser_mediator (ParserMediator): mediates interactions between parsers
          and other components, such as storage and dfvfs.
      database (Optional[pyesedb.file]): ESE database.
      table (Optional[pyesedb.table]): table.

    Raises:
      ValueError: if the database or table value is missing.
    """
    if database is None:
      raise ValueError('Missing database value.')

    if table is None:
      raise ValueError('Missing table value.')

    for esedb_record in table.records:
      if parser_mediator.abort:
        break

      record_values = self._GetRecordValues(
          parser_mediator, table.name, esedb_record)

      event_data = MsieWebCacheContainersEventData()
      event_data.container_identifier = record_values.get('ContainerId', None)
      event_data.directory = record_values.get('Directory', None)
      event_data.name = record_values.get('Name', None)
      event_data.set_identifier = record_values.get('SetId', None)

      timestamp = record_values.get('LastScavengeTime', None)
      if timestamp:
        date_time = dfdatetime_filetime.Filetime(timestamp=timestamp)
        event = time_events.DateTimeValuesEvent(
            date_time, 'Last Scavenge Time')
        parser_mediator.ProduceEventWithEventData(event, event_data)

      timestamp = record_values.get('LastAccessTime', None)
      if timestamp:
        date_time = dfdatetime_filetime.Filetime(timestamp=timestamp)
        event = time_events.DateTimeValuesEvent(
            date_time, definitions.TIME_DESCRIPTION_LAST_ACCESS)
        parser_mediator.ProduceEventWithEventData(event, event_data)

      container_identifier = record_values.get('ContainerId', None)
      container_name = record_values.get('Name', None)

      if not container_identifier or not container_name:
        continue

      if container_name in self._IGNORED_CONTAINER_NAMES:
        parser_mediator.ProduceExtractionWarning(
            'Skipped container (ContainerId: {0:d}, Name: {1:s})'.format(
                container_identifier, container_name))
        continue

      table_name = 'Container_{0:d}'.format(container_identifier)
      esedb_table = database.get_table_by_name(table_name)
      if not esedb_table:
        parser_mediator.ProduceExtractionWarning(
            'Missing table: {0:s}'.format(table_name))
        continue

      self._ParseContainerTable(parser_mediator, esedb_table, container_name)

  def ParseLeakFilesTable(
      self, parser_mediator, database=None, table=None, **unused_kwargs):
    """Parses a LeakFiles table.

    Args:
      parser_mediator (ParserMediator): mediates interactions between parsers
          and other components, such as storage and dfvfs.
      database (Optional[pyesedb.file]): ESE database.
      table (Optional[pyesedb.table]): table.

    Raises:
      ValueError: if the database or table value is missing.
    """
    if database is None:
      raise ValueError('Missing database value.')

    if table is None:
      raise ValueError('Missing table value.')

    for esedb_record in table.records:
      if parser_mediator.abort:
        break

      record_values = self._GetRecordValues(
          parser_mediator, table.name, esedb_record)

      event_data = MsieWebCacheLeakFilesEventData()
      event_data.cached_filename = record_values.get('Filename', None)
      event_data.leak_identifier = record_values.get('LeakId', None)

      timestamp = record_values.get('CreationTime', None)
      if timestamp:
        date_time = dfdatetime_filetime.Filetime(timestamp=timestamp)
        event = time_events.DateTimeValuesEvent(
            date_time, definitions.TIME_DESCRIPTION_CREATION)
        parser_mediator.ProduceEventWithEventData(event, event_data)

  def ParsePartitionsTable(
      self, parser_mediator, database=None, table=None, **unused_kwargs):
    """Parses a Partitions or PartitionsEx table.

    Args:
      parser_mediator (ParserMediator): mediates interactions between parsers
          and other components, such as storage and dfvfs.
      database (Optional[pyesedb.file]): ESE database.
      table (Optional[pyesedb.table]): table.

    Raises:
      ValueError: if the database or table value is missing.
    """
    if database is None:
      raise ValueError('Missing database value.')

    if table is None:
      raise ValueError('Missing table value.')

    for esedb_record in table.records:
      if parser_mediator.abort:
        break

      record_values = self._GetRecordValues(
          parser_mediator, table.name, esedb_record)

      event_data = MsieWebCachePartitionsEventData()
      event_data.directory = record_values.get('Directory', None)
      event_data.partition_identifier = record_values.get('PartitionId', None)
      event_data.partition_type = record_values.get('PartitionType', None)
      event_data.table_identifier = record_values.get('TableId', None)

      timestamp = record_values.get('LastScavengeTime', None)
      if timestamp:
        date_time = dfdatetime_filetime.Filetime(timestamp=timestamp)
        event = time_events.DateTimeValuesEvent(
            date_time, 'Last Scavenge Time')
        parser_mediator.ProduceEventWithEventData(event, event_data)


esedb.ESEDBParser.RegisterPlugin(MsieWebCacheESEDBPlugin)
