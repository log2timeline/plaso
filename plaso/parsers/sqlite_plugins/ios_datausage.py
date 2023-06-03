# -*- coding: utf-8 -*-
"""SQLite parser plugin for iOS datausage.sqlite database files."""

from dfdatetime import cocoa_time as dfdatetime_cocoa_time

from plaso.containers import events
from plaso.parsers import sqlite
from plaso.parsers.sqlite_plugins import interface


class IOSDatausageEventData(events.EventData):
  """iOS datausage event data.
  
  Attributes:
    bundle_identifier (str): bundle identifier.
    process_name (str): name of the process.
    start_time (dfdatetime.DateTimeValues): date and time the start of
        the network connection was established.
    wifi_in (int): number of bytes received over Wi-Fi.
    wifi_out (int): number of bytes sent over Wi-Fi.
    wireless_wan_in (int): number of bytes received over cellular.
    wireless_wan_out (int): number of bytes sent over cellular.
  """
  DATA_TYPE = 'ios:datausage:event'

  def __init__(self):
    """Initializes event data."""
    super(IOSDatausageEventData, self).__init__(data_type=self.DATA_TYPE)
    self.bundle_identifier = None
    self.process_name = None
    self.start_time = None
    self.wifi_in = None
    self.wifi_out = None
    self.wireless_wan_in = None
    self.wireless_wan_out = None


class IOSDatausagePlugin(interface.SQLitePlugin):
  """SQLite parser plugin for iOS DataUsage database."""

  NAME = "ios_datausage"
  DATA_FORMAT = 'iOS data usage SQLite databse (DataUsage.sqlite) file.'

  REQUIRED_STRUCTURE = {
      'ZLIVEUSAGE': frozenset([
          'Z_PK', 'Z_ENT', 'Z_OPT', 'ZKIND', 'ZMETADATA', 'ZTAG', 'ZHASPROCESS',
          'ZTIMESTAMP', 'ZWIFIIN', 'ZWIFIOUT', 'ZWWANIN', 'ZWWANOUT']),
      'ZPROCESS': frozenset([
          'Z_PK', 'Z_ENT', 'Z_OPT', 'ZFIRSTTIMESTAMP', 'ZTIMESTAMP',
          'ZBUNDLENAME', 'ZPROCNAME'])}

  QUERIES = [(
      ('SELECT ZLIVEUSAGE.ZTIMESTAMP, ZLIVEUSAGE.ZWIFIIN, ZLIVEUSAGE.ZWIFIOUT, '
       'ZLIVEUSAGE.ZWWANIN, ZLIVEUSAGE.ZWWANOUT, ZPROCESS.ZBUNDLENAME, '
       'ZPROCESS.ZPROCNAME FROM ZLIVEUSAGE '
       'LEFT JOIN ZPROCESS ON ZPROCESS.Z_PK = ZLIVEUSAGE.ZHASPROCESS'),
     'ParseDatausageEventRow')]

  SCHEMAS = {
    'ZLIVEUSAGE': (
        'CREATE TABLE ZLIVEUSAGE ( Z_PK INTEGER PRIMARY KEY, Z_ENT INTEGER, '
        'Z_OPT INTEGER, ZKIND INTEGER, ZMETADATA INTEGER, ZTAG INTEGER, '
        'ZHASPROCESS INTEGER, ZBILLCYCLEEND TIMESTAMP, ZTIMESTAMP TIMESTAMP, '
        'ZWIFIIN FLOAT, ZWIFIOUT FLOAT, ZWWANIN FLOAT, ZWWANOUT FLOAT )'),
    'ZPROCESS': (
        'CREATE TABLE ZPROCESS ( Z_PK INTEGER PRIMARY KEY, Z_ENT INTEGER, '
        'Z_OPT INTEGER, ZFIRSTTIMESTAMP TIMESTAMP, ZTIMESTAMP TIMESTAMP, '
        'ZBUNDLENAME VARCHAR, ZPROCNAME VARCHAR )')}

  REQUIRES_SCHEMA_MATCH = False

  def _GetTimeRowValue(self, query_hash, row, value_name):
    """Retrieves a date and time value from the row.

    Args:
      query_hash (int): hash of the query, that uniquely identifies the query
          that produced the row.
      row (sqlite3.Row): row.
      value_name (str): name of the value.

    Returns:
      dfdatetime.CocoaTime: date and time value or None if not available.
    """
    timestamp = self._GetRowValue(query_hash, row, value_name)
    if timestamp is None:
      return None

    return dfdatetime_cocoa_time.CocoaTime(timestamp=timestamp)

  # pylint: disable=unused-argument
  def ParseDatausageEventRow(
        self, parser_mediator, query, row, **unused_kwargs):
    """Parses a row from the Datausage sqlite file.
    Args:
      parser_mediator (ParserMediator): mediates interactions between parsers
          and other components, such as storage and dfVFS.
      query (str): query that created the row.
      row (sqlite3.Row): row.
    """
    query_hash = hash(query)

    event_data = IOSDatausageEventData()
    event_data.bundle_identifier = self._GetRowValue(
        query_hash, row, 'ZBUNDLENAME')
    event_data.process_name = self._GetRowValue(self, row, 'ZPROCNAME')
    event_data.start_time = self._GetTimeRowValue(self, row, 'ZTIMESTAMP')
    event_data.wifi_in = int(self._GetRowValue(self, row, 'ZWIFIIN'))
    event_data.wifi_out = int(self._GetRowValue(self, row, 'ZWIFIOUT'))
    event_data.wireless_wan_in = int(self._GetRowValue(self, row, 'ZWWANIN'))
    event_data.wireless_wan_out = int(self._GetRowValue(self, row, 'ZWWANOUT'))

    parser_mediator.ProduceEventData(event_data)


sqlite.SQLiteParser.RegisterPlugin(IOSDatausagePlugin)
