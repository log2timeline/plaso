# -*- coding: utf-8 -*-
"""Parser for the Microsoft Internet Explorer WebCache ESE database.

The WebCache database (WebCacheV01.dat or WebCacheV24.dat) are used by MSIE
as of version 10.
"""

from dfdatetime import filetime as dfdatetime_filetime
from dfdatetime import semantic_time as dfdatetime_semantic_time

from plaso.containers import events
from plaso.lib import cookie_plugins_helper
from plaso.parsers import esedb
from plaso.parsers.esedb_plugins import interface


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

  DATA_TYPE = 'msie:cookie:entry'

  def __init__(self):
    """Initializes event data."""
    super(MsieWebCacheCookieData, self).__init__(
        data_type=self.DATA_TYPE)
    self.container_identifier = None
    self.cookie_hash = None
    self.cookie_name = None
    self.cookie_value_raw = None
    self.cookie_value = None
    self.entry_identifier = None
    self.expiration_time = None
    self.flags = None
    self.modification_time = None
    self.request_domain = None


class MSIE11CookiePlugin(
    interface.ESEDBPlugin, cookie_plugins_helper.CookiePluginsHelper):
  """SQLite parser plugin for Internet cookies in the MSIE webcache file."""

  NAME = 'msie_webcache_cookies'
  DATA_FORMAT = (
      'Internet Explorer WebCache ESE database (WebCacheV01.dat, '
      'WebCacheV24.dat) file')
  REQUIRED_TABLES = {
      'Containers': 'ParseContainersTableCookie',
  }

  def _GetDateTimeValue(self, record_values, value_name):
    """Retrieves a date and time record value.

    Args:
      record_values (dict[str,object]): values per column name.
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

  def _CookieHexToAscii(self, raw_cookie):
    """Translates a cookie from a bytestring to a string"""
    if raw_cookie is not None:
      raw_cookie = raw_cookie.rstrip(b'\x00')
      return raw_cookie.decode('ascii')
    return None

  def GetRawCookieValue(self, record_values, value_name):
    """return the binary string as a hex string"""
    cookie_hash = record_values.get(value_name, None)
    if cookie_hash is not None:
      return f"0x{cookie_hash.hex()}"
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

  def ParseContainersTableCookie(
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
      container_identifier = record_values.get('ContainerId', None)
      # Each Container table may have a CookieEx table attached to it.
      cookie_table_name = 'CookieEntryEx_{0:d}'.format(container_identifier)
      cookie_table = database.GetTableByName(cookie_table_name)
      if cookie_table.name==cookie_table_name:
        self._ParseCookieExTable(parser_mediator, cookie_table)


esedb.ESEDBParser.RegisterPlugin(MSIE11CookiePlugin)
