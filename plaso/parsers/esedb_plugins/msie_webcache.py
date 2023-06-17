# -*- coding: utf-8 -*-
"""Parser for the Microsoft Internet Explorer WebCache ESE database.

The WebCache database (WebCacheV01.dat or WebCacheV24.dat) are used by MSIE
as of version 10.
"""

from dfdatetime import filetime as dfdatetime_filetime
from dfdatetime import semantic_time as dfdatetime_semantic_time

from plaso.containers import events
from plaso.parsers import esedb
from plaso.parsers.esedb_plugins import interface


class MsieWebCacheContainersEventData(events.EventData):
  """MSIE WebCache Containers table event data.

  Attributes:
    access_time (dfdatetime.DateTimeValues): last access date and time.
    container_identifier (int): container identifier.
    directory (str): name of the cache directory.
    name (str): name of the cache container.
    scavenge_time (dfdatetime.DateTimeValues): last scavenge date and time.
    set_identifier (int): set identifier.
  """

  DATA_TYPE = 'msie:webcache:containers'

  def __init__(self):
    """Initializes event data."""
    super(MsieWebCacheContainersEventData, self).__init__(
        data_type=self.DATA_TYPE)
    self.access_time = None
    self.container_identifier = None
    self.directory = None
    self.name = None
    self.scavenge_time = None
    self.set_identifier = None


class MsieWebCacheContainerEventData(events.EventData):
  """MSIE WebCache Container table event data.

  Attributes:
    access_count (int): access count.
    access_time (dfdatetime.DateTimeValues): last access date and time.
    cached_filename (str): name of the cached file.
    cached_file_size (int): size of the cached file.
    cache_identifier (int): cache identifier.
    container_identifier (int): container identifier.
    creation_time (dfdatetime.DateTimeValues): creation date and time.
    entry_identifier (int): entry identifier.
    expiration_time (dfdatetime.DateTimeValues): expiration date and time.
    file_extension (str): file extension.
    modification_time (dfdatetime.DateTimeValues): modification date and time.
    post_check_time (dfdatetime.DateTimeValues): post check date and time.
    redirect_url (str): URL from which the request was redirected.
    request_headers (str): request headers.
    response_headers (str): response headers.
    synchronization_count (int): synchronization count.
    synchronization_time (dfdatetime.DateTimeValues): synchronization date
        and time.
    url (str): URL.
  """

  DATA_TYPE = 'msie:webcache:container'

  def __init__(self):
    """Initializes event data."""
    super(MsieWebCacheContainerEventData, self).__init__(
        data_type=self.DATA_TYPE)
    self.access_count = None
    self.access_time = None
    self.cached_filename = None
    self.cached_file_size = None
    self.cache_identifier = None
    self.container_identifier = None
    self.creation_time = None
    self.entry_identifier = None
    self.expiration_time = None
    self.file_extension = None
    self.modification_time = None
    self.post_check_time = None
    self.redirect_url = None
    self.request_headers = None
    self.response_headers = None
    self.synchronization_count = None
    self.synchronization_time = None
    self.url = None


class MsieWebCacheCookieData(events.EventData):
  """MSIE WebCache Container table event data.

  Attributes:
    container_identifier (int): container identifier.
    cookie_hash (str): a similarity hash of the cookie contents
    cookie_name (str): name of the cookie
    cookie_value_raw (str): raw value of cookie in hex
    cookie_value (str): value of the cookie encoded in ascii
    entry_identifier (int): entry identifier.
    expiration_time (dfdatetime.DateTimeValues): expiration date and time.
    flags (int): an representation of cookie flags
    modification_time (dfdatetime.DateTimeValues): modification date and time.
    request_domain (str): Request domain for which the cookie was set.
  """

  DATA_TYPE = 'msie:webcache:cookie'

  def __init__(self):
    """Initializes event data."""
    super(MsieWebCacheCookieData, self).__init__(data_type=self.DATA_TYPE)
    self.container_identifier = None
    self.cookie_hash = None
    self.cookie_name = None
    self.cookie_value = None
    self.cookie_value_raw = None
    self.entry_identifier = None
    self.expiration_time = None
    self.flags = None
    self.modification_time = None
    self.request_domain = None


class MsieWebCacheLeakFilesEventData(events.EventData):
  """MSIE WebCache LeakFiles event data.

  Attributes:
    cached_filename (str): name of the cached file.
    creation_time (dfdatetime.DateTimeValues): creation date and time.
    leak_identifier (int): leak identifier.
  """

  DATA_TYPE = 'msie:webcache:leak_file'

  def __init__(self):
    """Initializes event data."""
    super(MsieWebCacheLeakFilesEventData, self).__init__(
        data_type=self.DATA_TYPE)
    self.cached_filename = None
    self.creation_time = None
    self.leak_identifier = None


class MsieWebCachePartitionsEventData(events.EventData):
  """MSIE WebCache Partitions table event data.

  Attributes:
    directory (str): directory.
    partition_identifier (int): partition identifier.
    partition_type (int): partition type.
    scavenge_time (dfdatetime.DateTimeValues): last scavenge date and time.
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
    self.scavenge_time = None
    self.table_identifier = None


class MsieWebCacheESEDBPlugin(interface.ESEDBPlugin):
  """Parses a MSIE WebCache ESE database file."""

  NAME = 'msie_webcache'
  DATA_FORMAT = (
      'Internet Explorer WebCache ESE database (WebCacheV01.dat, '
      'WebCacheV24.dat) file')

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
      'BackgroundTransferApi', 'Content', 'Cookies', 'DOMStore', 'History',
      'iedownload'])

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
      value = value.decode('utf-8')
      header_values = [value.strip() for value in value.split('\r\n') if value]
      return '[{0:s}]'.format('; '.join(header_values))

    return None

  def _GetDateTimeValue(self, record_values, value_name):
    """Retrieves a date and time record value.

    Args:
      record_values (dict[str, object]): values per column name.
      value_name (str): name of the record value.

    Returns:
      dfdatetime.DateTimeValues: date and time or None if not set.
    """
    filetime = record_values.get(value_name, None)
    if not filetime:
      return None

    # TODO: add support for filetime == 1 and other edge cases.

    if filetime == 0x7fffffffffffffff:
      return dfdatetime_semantic_time.SemanticTime(string='Infinite')

    return dfdatetime_filetime.Filetime(timestamp=filetime)

  def _ParseContainerTable(self, parser_mediator, table, container_name):
    """Parses a Container_# table.

    Args:
      parser_mediator (ParserMediator): mediates interactions between parsers
          and other components, such as storage and dfVFS.
      table (pyesedb.table): table.
      container_name (str): container name, which indicates the table type.
    """
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
            parser_mediator, table.name, record_index, esedb_record,
            value_mappings=value_mappings)

      except UnicodeDecodeError:
        parser_mediator.ProduceExtractionWarning((
            'Unable to retrieve record values from record: {0:d} '
            'in table: {1:s}').format(record_index, table.name))
        continue

      if (container_name in self._SUPPORTED_CONTAINER_NAMES or
          container_name.startswith('MSHist')):
        url = record_values.get('Url', '')
        # Ignore a URL that start with a binary value.
        if ord(url[0]) < 0x20 or ord(url[0]) == 0x7f:
          url = None

        request_headers = record_values.get('RequestHeaders', None)
        # Ignore non-Unicode request headers values.
        if not isinstance(request_headers, str):
          request_headers = None

        response_headers = record_values.get('ResponseHeaders', None)
        # Ignore non-Unicode response headers values.
        if not isinstance(response_headers, str):
          response_headers = None

        event_data = MsieWebCacheContainerEventData()
        event_data.access_count = record_values.get('AccessCount', None)
        event_data.access_time = self._GetDateTimeValue(
            record_values, 'AccessedTime')
        event_data.cached_filename = record_values.get('Filename', None)
        event_data.cached_file_size = record_values.get('FileSize', None)
        event_data.cache_identifier = record_values.get('CacheId', None)
        event_data.container_identifier = record_values.get('ContainerId', None)
        event_data.creation_time = self._GetDateTimeValue(
            record_values, 'CreationTime')
        event_data.entry_identifier = record_values.get('EntryId', None)
        event_data.expiration_time = self._GetDateTimeValue(
            record_values, 'ExpiryTime')
        event_data.file_extension = record_values.get('FileExtension', None)
        event_data.modification_time = self._GetDateTimeValue(
            record_values, 'ModifiedTime')
        event_data.post_check_time = self._GetDateTimeValue(
            record_values, 'PostCheckTime')
        event_data.redirect_url = record_values.get('RedirectUrl', None)
        event_data.request_headers = request_headers
        event_data.response_headers = response_headers
        event_data.synchronization_count = record_values.get('SyncCount', None)
        event_data.synchronization_time = self._GetDateTimeValue(
            record_values, 'SyncTime')
        event_data.url = url

        parser_mediator.ProduceEventData(event_data)

  def _CookieHexToAscii(self, raw_cookie):
    """Translates a cookie from a binary string to a string.

    Args:
      raw_cookie (bytes): the raw binary string of a cookie field.

    Returns:
      str: the decoded binary string or None if not available.
    """
    if raw_cookie is not None:
      try:
        string_value = raw_cookie.decode('utf-8')
        return string_value.rstrip('\x00')
      except UnicodeDecodeError:
        pass

    return None

  def GetRawCookieValue(self, record_values, value_name):
    """Retrieves the binary string as a hexadecimal formatted string.
      
    Args:
      record_values (dict[str, object]): values per column name.
      value_name (str): the name of the value we are converting

    Returns:
      str: the hexadecimal formatted binary string or None if not available.
    """
    cookie_hash = record_values.get(value_name, None)
    if cookie_hash is not None:
      return cookie_hash.hex()
    return None

  def _ParseCookieExTable(self, parser_mediator, table):
    """Parses a CookieEntryEx_# table.

    Args:
      parser_mediator (ParserMediator): mediates interactions between parsers
          and other components, such as storage and dfVFS.
      table (pyesedb.table): table.
      container_name (str): container name, which indicates the table type.
    """
    for record_index, esedb_record in enumerate(table.records):
      if parser_mediator.abort:
        break

      try:
        record_values = self._GetRecordValues(
            parser_mediator, table.name, record_index, esedb_record)

      except UnicodeDecodeError:
        parser_mediator.ProduceExtractionWarning((
            'Unable to retrieve record values from record: {0:d} '
            'in table: {1:s}').format(record_index, table.name))
        continue

      cookie_name = self._CookieHexToAscii(record_values.get('Name', None))
      cookie_value = self._CookieHexToAscii(record_values.get('Value', None))

      cookie_hash = self.GetRawCookieValue(record_values, 'CookieHash')
      cookie_value_raw = self.GetRawCookieValue(record_values, 'Value')

      event_data = MsieWebCacheCookieData()
      event_data.container_identifier = record_values.get('ContainerId', None)
      event_data.cookie_hash = cookie_hash
      event_data.cookie_name = cookie_name
      event_data.cookie_value_raw = cookie_value_raw
      event_data.cookie_value = cookie_value
      event_data.entry_identifier = record_values.get('EntryId', None)
      event_data.flags = record_values.get('Flags', None)
      event_data.expiration_time = self._GetDateTimeValue(
          record_values, 'Expires')
      event_data.modification_time = self._GetDateTimeValue(
          record_values, 'LastModified')
      event_data.request_domain = record_values.get('RDomain', None)
      parser_mediator.ProduceEventData(event_data)

  def ParseContainersTable(
      self, parser_mediator, database=None, table=None, **unused_kwargs):
    """Parses a Containers table.

    Args:
      parser_mediator (ParserMediator): mediates interactions between parsers
          and other components, such as storage and dfVFS.
      database (Optional[ESEDatabase]): ESE database.
      table (Optional[pyesedb.table]): table.

    Raises:
      ValueError: if the database or table value is missing.
    """
    if database is None:
      raise ValueError('Missing database value.')

    if table is None:
      raise ValueError('Missing table value.')

    for record_index, esedb_record in enumerate(table.records):
      if parser_mediator.abort:
        break

      record_values = self._GetRecordValues(
          parser_mediator, table.name, record_index, esedb_record)

      event_data = MsieWebCacheContainersEventData()
      event_data.access_time = self._GetDateTimeValue(
          record_values, 'LastAccessTime')
      event_data.container_identifier = record_values.get('ContainerId', None)
      event_data.directory = record_values.get('Directory', None)
      event_data.name = record_values.get('Name', None)
      event_data.scavenge_time = self._GetDateTimeValue(
          record_values, 'LastScavengeTime')
      event_data.set_identifier = record_values.get('SetId', None)

      parser_mediator.ProduceEventData(event_data)

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
      esedb_table = database.GetTableByName(table_name)
      if esedb_table:
        self._ParseContainerTable(parser_mediator, esedb_table, container_name)
      cookie_table_name = 'CookieEntryEx_{0:d}'.format(container_identifier)
      cookie_table = database.GetTableByName(cookie_table_name)
      if cookie_table.name==cookie_table_name:
        self._ParseCookieExTable(parser_mediator, cookie_table)

  def ParseLeakFilesTable(
      self, parser_mediator, database=None, table=None, **unused_kwargs):
    """Parses a LeakFiles table.

    Args:
      parser_mediator (ParserMediator): mediates interactions between parsers
          and other components, such as storage and dfVFS.
      database (Optional[ESEDatabase]): ESE database.
      table (Optional[pyesedb.table]): table.

    Raises:
      ValueError: if the database or table value is missing.
    """
    if database is None:
      raise ValueError('Missing database value.')

    if table is None:
      raise ValueError('Missing table value.')

    for record_index, esedb_record in enumerate(table.records):
      if parser_mediator.abort:
        break

      record_values = self._GetRecordValues(
          parser_mediator, table.name, record_index, esedb_record)

      event_data = MsieWebCacheLeakFilesEventData()
      event_data.cached_filename = record_values.get('Filename', None)
      event_data.creation_time = self._GetDateTimeValue(
          record_values, 'CreationTime')
      event_data.leak_identifier = record_values.get('LeakId', None)

      parser_mediator.ProduceEventData(event_data)

  def ParsePartitionsTable(
      self, parser_mediator, database=None, table=None, **unused_kwargs):
    """Parses a Partitions or PartitionsEx table.

    Args:
      parser_mediator (ParserMediator): mediates interactions between parsers
          and other components, such as storage and dfVFS.
      database (Optional[ESEDatabase]): ESE database.
      table (Optional[pyesedb.table]): table.

    Raises:
      ValueError: if the database or table value is missing.
    """
    if database is None:
      raise ValueError('Missing database value.')

    if table is None:
      raise ValueError('Missing table value.')

    for record_index, esedb_record in enumerate(table.records):
      if parser_mediator.abort:
        break

      record_values = self._GetRecordValues(
          parser_mediator, table.name, record_index, esedb_record)

      event_data = MsieWebCachePartitionsEventData()
      event_data.directory = record_values.get('Directory', None)
      event_data.partition_identifier = record_values.get('PartitionId', None)
      event_data.partition_type = record_values.get('PartitionType', None)
      event_data.scavenge_time = self._GetDateTimeValue(
          record_values, 'LastScavengeTime')
      event_data.table_identifier = record_values.get('TableId', None)

      parser_mediator.ProduceEventData(event_data)


esedb.ESEDBParser.RegisterPlugin(MsieWebCacheESEDBPlugin)
