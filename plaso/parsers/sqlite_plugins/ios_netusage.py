# -*- coding: utf-8 -*-
"""SQLite parser plugin for iOS netusage.sqlite database files."""

from dfdatetime import cocoa_time as dfdatetime_cocoa_time

from plaso.containers import events
from plaso.parsers import sqlite
from plaso.parsers.sqlite_plugins import interface


class IOSNetusageProcessEventData(events.EventData):
  """iOS netusage process event data.

  Attributes:
    process_name (str): name of the process.
    start_time (dfdatetime.DateTimeValues): date and time the start of
        the network connection was established.
    wifi_in (int): bytes received via wifi.
    wifi_out (int): bytes sent via wifi.
    wired_in (int): bytes received via wired connection.
    wired_out (int): bytes sent via wired connection.
    wireless_wan_in (int): bytes received via cellular connection.
    wireless_wan_out (int): bytes sent via cellular connection.
  """
  DATA_TYPE = 'ios:netusage:process'

  def __init__(self):
    """Initializes event data."""
    super(IOSNetusageProcessEventData, self).__init__(data_type=self.DATA_TYPE)
    self.process_name = None
    self.start_time = None
    self.wifi_in = None
    self.wifi_out = None
    self.wired_in = None
    self.wired_out = None
    self.wireless_wan_in = None
    self.wireless_wan_out = None


class IOSNetusageRouteEventData(events.EventData):
  """iOS netusage connection event data.

  Attributes:
    bytes_in (int): number of bytes received.
    bytes_out (int): number of bytes sent.
    network_identifier (str): name of network.
    network_signature (str): signature of network.
    network_type (int): integer indicating network type.
    start_time (dfdatetime.DateTimeValues): date and time the start of
        the network connection was established.
  """

  DATA_TYPE = 'ios:netusage:route'

  def __init__(self):
    """Initializes event data."""
    super(IOSNetusageRouteEventData, self).__init__(data_type=self.DATA_TYPE)
    self.bytes_in = None
    self.bytes_out = None
    self.network_identifier = None
    self.network_signature = None
    self.network_type = None
    self.start_time = None


class IOSNetusagePlugin(interface.SQLitePlugin):
  """SQLite parser plugin for iOS netusage database."""

  NAME = 'ios_netusage'
  DATA_FORMAT = 'iOS network usage SQLite database (netusage.sqlite) file'

  REQUIRED_STRUCTURE = {
      'ZLIVEROUTEPERF': frozenset([
          'ZTIMESTAMP', 'ZKIND', 'ZBYTESIN', 'ZBYTESOUT',
          'ZHASNETWORKATTACHMENT']),
      'ZNETWORKATTACHMENT': frozenset(['Z_PK', 'ZIDENTIFIER', 'ZNETSIGNATURE']),
      'ZLIVEUSAGE': frozenset([
          'ZTIMESTAMP', 'ZWIFIIN', 'ZWIFIOUT', 'ZWWANIN', 'ZWWANOUT',
          'ZWIREDIN', 'ZWIREDOUT', 'ZHASPROCESS']),
      'ZPROCESS': frozenset(['Z_PK', 'ZPROCNAME'])}

  QUERIES = [
      ("""
       SELECT 
         ZLIVEROUTEPERF.ZTIMESTAMP, 
         ZLIVEROUTEPERF.ZKIND, 
         ZLIVEROUTEPERF.ZBYTESIN, 
         ZLIVEROUTEPERF.ZBYTESOUT, 
         ZNETWORKATTACHMENT.ZIDENTIFIER, 
         HEX(ZNETWORKATTACHMENT.ZNETSIGNATURE) as ZNETSIGNATURE
       FROM ZLIVEROUTEPERF
       LEFT JOIN ZNETWORKATTACHMENT 
       ON ZLIVEROUTEPERF.ZHASNETWORKATTACHMENT = ZNETWORKATTACHMENT.Z_PK""",
       'ParseNetusageRouteRow'),
      ("""
         SELECT
           ZLIVEUSAGE.ZTIMESTAMP,
           ZPROCESS.ZPROCNAME,
           ZLIVEUSAGE.ZWIFIIN,
           ZLIVEUSAGE.ZWIFIOUT,
           ZLIVEUSAGE.ZWWANIN,
           ZLIVEUSAGE.ZWWANOUT,
           ZLIVEUSAGE.ZWIREDIN,
           ZLIVEUSAGE.ZWIREDOUT
         FROM ZLIVEUSAGE 
         LEFT JOIN ZPROCESS 
         ON ZPROCESS.Z_PK = ZLIVEUSAGE.ZHASPROCESS""",
      'ParseNetusageProcessRow')
  ]

  SCHEMAS = {
      'ZLIVEROUTEPERF': (
          'CREATE TABLE ZLIVEROUTEPERF (Z_PK INTEGER PRIMARY KEY, '
          'Z_ENT INTEGER, Z_OPT INTEGER, ZKIND INTEGER, ZHASNETWORKATTACHMENT '
          'INTEGER, ZADMINDISABLES FLOAT, ZBYTESIN FLOAT, ZBYTESOUT FLOAT, '
          'ZCAPTIVITYREDIRECTS FLOAT, ZCERTERRORS FLOAT, ZCONNATTEMPTS FLOAT, '
          'ZCONNSUCCESSES FLOAT, ZDATASTALLS FLOAT, ZEPOCHS FLOAT, ZFAULTYSTAY '
          'FLOAT, ZLOWLQMSTAY FLOAT, ZLOWQSTAY FLOAT, ZLQMTRANSITIONCOUNT '
          'FLOAT, ZOVERALLSTAY FLOAT, ZOVERALLSTAYM2 FLOAT, ZPACKETSIN FLOAT, '
          'ZPACKETSOUT FLOAT, ZRETXBYTES FLOAT, ZRTTAVG FLOAT, ZRTTMIN FLOAT, '
          'ZRTTVAR FLOAT, ZRXDUPEBYTES FLOAT, ZRXOOOBYTES FLOAT, ZTIMESTAMP '
          'TIMESTAMP, ZTOPDOWNLOADRATE FLOAT )'),
      'ZNETWORKATTACHMENT': (
          'CREATE TABLE ZNETWORKATTACHMENT ( Z_PK INTEGER PRIMARY KEY, '
          'Z_ENT INTEGER, Z_OPT INTEGER, ZATTRS INTEGER, ZISHOTSPOT INTEGER, '
          'ZISKNOWNGOOD INTEGER, ZISLOWINTERNETDL INTEGER, '
          'ZISLOWINTERNETUL INTEGER, ZKIND INTEGER, ZWASLASTFAILED INTEGER, '
          'ZFIRSTTIMESTAMP TIMESTAMP, ZOVERALLSTAYMEAN FLOAT, '
          'ZOVERALLSTAYVAR FLOAT, ZTIMESTAMP TIMESTAMP, ZVELO FLOAT, '
          'ZIDENTIFIER VARCHAR, ZSERVICE VARCHAR, ZNETSIGNATURE BLOB )'),
      'ZLIVEUSAGE': (
          'CREATE TABLE ZLIVEUSAGE ( Z_PK INTEGER PRIMARY KEY, Z_ENT INTEGER, '
          'Z_OPT INTEGER, ZKIND INTEGER, ZMETADATA INTEGER, ZTAG INTEGER, '
          'ZHASPROCESS INTEGER, Z15_HASPROCESS INTEGER, ZALLFLOWS FLOAT, '
          'ZBILLCYCLEEND TIMESTAMP, ZJUMBOFLOWS FLOAT, ZTIMESTAMP TIMESTAMP, '
          'ZWIFIIN FLOAT, ZWIFIOUT FLOAT, ZWIREDIN FLOAT, ZWIREDOUT FLOAT, '
          'ZWWANIN FLOAT, ZWWANOUT FLOAT, ZXIN FLOAT, ZXOUT FLOAT )'),
      'ZPROCESS': (
          'CREATE TABLE ZPROCESS ( Z_PK INTEGER PRIMARY KEY, Z_ENT INTEGER, '
          'Z_OPT INTEGER, ZFIRSTTIMESTAMP TIMESTAMP, ZTIMESTAMP TIMESTAMP, '
          'ZBUNDLENAME VARCHAR, ZPROCNAME VARCHAR )')}

  REQUIRES_SCHEMA_MATCH = False

  def _GetDateTimeRowValue(self, query_hash, row, value_name):
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
  def ParseNetusageRouteRow(self, parser_mediator, query, row, **unused_kwargs):
    """Parses a Netusage route row.

    Args:
      parser_mediator (ParserMediator): mediates interactions between parsers
          and other components, such as storage and dfVFS.
      query (str): query that created the row.
      row (sqlite3.Row): row.
    """
    query_hash = hash(query)

    event_data = IOSNetusageRouteEventData()
    event_data.bytes_in = int(self._GetRowValue(query_hash, row, 'ZBYTESIN'))
    event_data.bytes_out = int(self._GetRowValue(query_hash, row, 'ZBYTESOUT'))
    event_data.network_identifier = self._GetRowValue(
        query_hash, row, 'ZIDENTIFIER')
    event_data.network_signature = self._GetRowValue(
        query_hash, row, 'ZNETSIGNATURE')
    event_data.network_type = self._GetRowValue(query_hash, row, 'ZKIND')
    event_data.start_time = self._GetDateTimeRowValue(
        query_hash, row, 'ZTIMESTAMP')

    parser_mediator.ProduceEventData(event_data)

  # pylint: disable=unused-argument
  def ParseNetusageProcessRow(
      self, parser_mediator, query, row, **unused_kwargs):
    """Parses a Netusage process row.

    Args:
      parser_mediator (ParserMediator): mediates interactions between parsers
          and other components, such as storage and dfVFS.
      query (str): query that created the row.
      row (sqlite3.Row): row.
    """
    query_hash = hash(query)

    event_data = IOSNetusageProcessEventData()
    event_data.process_name = self._GetRowValue(query_hash, row, 'ZPROCNAME')
    event_data.start_time = self._GetDateTimeRowValue(
        query_hash, row, 'ZTIMESTAMP')
    event_data.wifi_in = int(self._GetRowValue(query_hash, row, 'ZWIFIIN'))
    event_data.wifi_out = int(self._GetRowValue(query_hash, row, 'ZWIFIOUT'))
    event_data.wired_in = int(self._GetRowValue(query_hash, row, 'ZWIREDIN'))
    event_data.wired_out = int(self._GetRowValue(query_hash, row, 'ZWIREDOUT'))
    event_data.wireless_wan_in = int(self._GetRowValue(
        query_hash, row, 'ZWWANIN'))
    event_data.wireless_wan_out = int(self._GetRowValue(
        query_hash, row, 'ZWWANOUT'))

    parser_mediator.ProduceEventData(event_data)


sqlite.SQLiteParser.RegisterPlugin(IOSNetusagePlugin)
