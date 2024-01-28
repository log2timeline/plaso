# -*- coding: utf-8 -*-
"""SQLite parser plugin for iOS Screen Time database files."""

from dfdatetime import cocoa_time as dfdatetime_cocoa_time

from plaso.containers import events
from plaso.parsers import sqlite
from plaso.parsers.sqlite_plugins import interface


class IOSScreenTimeEventData(events.EventData):
  """iOS Screen Time file usage event data.

  Attributes:
    bundle_identifier (str): Bundle Identifier of the application.
    device_identifier (str): GUID for the device.
    device_name (str): Name of the device in use (when available).
    domain (str): Domain of the website visited.
    start_time (dfdatetime.DateTimeValues): date and time the start of
        the application.
    total_time (int): Number of seconds where the application was in the
        foreground.
    user_family_name (str): Family name of the user.
    user_given_name (str): Given name of the user.
  """

  DATA_TYPE = 'ios:screentime:event'

  def __init__(self):
    """Initializes event data."""
    super(IOSScreenTimeEventData, self).__init__(data_type=self.DATA_TYPE)
    self.bundle_identifier = None
    self.device_identifier = None
    self.device_name = None
    self.domain = None
    self.start_time = None
    self.total_time = None
    self.user_family_name = None
    self.user_given_name = None


class IOSScreenTimePlugin(interface.SQLitePlugin):
  """SQLite parser plugin for iOS Screen Time database files.

  The Screen Time database is typically stored in:
  RMAdminStore-Local.sqlite
  """

  NAME = 'ios_screentime'
  DATA_FORMAT = 'iOS Screen Time SQLite database (RMAdminStore-Local.sqlite)'

  REQUIRED_STRUCTURE = {
      'ZUSAGETIMEDITEM': frozenset([
          'ZBUNDLEIDENTIFIER', 'ZCATEGORY', 'ZDOMAIN', 'ZTOTALTIMEINSECONDS']),
      'ZUSAGECATEGORY': frozenset(['Z_PK', 'ZBLOCK']),
      'ZUSAGEBLOCK': frozenset(['Z_PK', 'ZSTARTDATE', 'ZUSAGE']),
      'ZUSAGE': frozenset(['Z_PK', 'ZDEVICE', 'ZUSER']),
      'ZCOREDEVICE': frozenset(['Z_PK', 'ZIDENTIFIER', 'ZNAME']),
      'ZCOREUSER': frozenset(['Z_PK', 'ZFAMILYNAME', 'ZGIVENNAME'])}

  QUERIES = [(
      """
      SELECT ZUSAGETIMEDITEM.ZTOTALTIMEINSECONDS,
        ZUSAGETIMEDITEM.ZBUNDLEIDENTIFIER,
        ZUSAGETIMEDITEM.ZDOMAIN,
        ZUSAGEBLOCK.ZSTARTDATE,
        ZCOREDEVICE.ZIDENTIFIER,
        ZCOREDEVICE.ZNAME,
        ZCOREUSER.ZFAMILYNAME,
        ZCOREUSER.ZGIVENNAME
      FROM ZUSAGETIMEDITEM
      LEFT JOIN ZUSAGECATEGORY
        ON ZUSAGETIMEDITEM.ZCATEGORY = ZUSAGECATEGORY.Z_PK
      LEFT JOIN ZUSAGEBLOCK ON ZUSAGECATEGORY.ZBLOCK = ZUSAGEBLOCK.Z_PK
      LEFT JOIN ZUSAGE ON ZUSAGEBLOCK.ZUSAGE = ZUSAGE.Z_PK
      LEFT JOIN ZCOREDEVICE ON ZUSAGE.ZDEVICE = ZCOREDEVICE.Z_PK
      LEFT JOIN ZCOREUSER ON ZUSAGE.ZUSER = ZCOREUSER.Z_PK
      """, 'ParseScreenTimeRow')]

  SCHEMAS = {
      'ZUSAGETIMEDITEM': (
          'CREATE TABLE ZUSAGETIMEDITEM ( Z_PK INTEGER PRIMARY KEY, '
          'Z_ENT INTEGER, Z_OPT INTEGER, ZTOTALTIMEINSECONDS INTEGER, '
          'ZUSAGETRUSTED INTEGER, ZCATEGORY INTEGER, ZBUNDLEIDENTIFIER VARCHAR,'
          ' ZDOMAIN VARCHAR )'),
      'ZUSAGECATEGORY': (
          'CREATE TABLE ZUSAGECATEGORY ( Z_PK INTEGER PRIMARY KEY, '
          'Z_ENT INTEGER, Z_OPT INTEGER, ZTOTALTIMEINSECONDS INTEGER, '
          'ZBLOCK INTEGER, ZIDENTIFIER VARCHAR )'),
      'ZUSAGEBLOCK': (
          'CREATE TABLE ZUSAGEBLOCK ( Z_PK INTEGER PRIMARY KEY, Z_ENT INTEGER, '
          'Z_OPT INTEGER, ZDURATIONINMINUTES INTEGER, '
          'ZNUMBEROFPICKUPSWITHOUTAPPLICATIONUSAGE INTEGER, '
          'ZSCREENTIMEINSECONDS INTEGER, ZUSAGE INTEGER, '
          'ZFIRSTPICKUPDATE TIMESTAMP, ZLASTEVENTDATE TIMESTAMP, '
          'ZLONGESTSESSIONENDDATE TIMESTAMP, '
          'ZLONGESTSESSIONSTARTDATE TIMESTAMP, ZSTARTDATE TIMESTAMP )'),
      'ZUSAGE': (
          'CREATE TABLE ZUSAGE ( Z_PK INTEGER PRIMARY KEY, Z_ENT INTEGER, '
          'Z_OPT INTEGER, ZDEVICE INTEGER, ZUSER INTEGER, '
          'ZLASTEVENTDATE TIMESTAMP, ZLASTUPDATEDDATE TIMESTAMP )'),
      'ZCOREDEVICE': (
          'CREATE TABLE ZCOREDEVICE ( Z_PK INTEGER PRIMARY KEY, Z_ENT INTEGER, '
          'Z_OPT INTEGER, ZPLATFORM INTEGER, ZLOCALUSERDEVICESTATE INTEGER, '
          'ZIDENTIFIER VARCHAR, ZNAME VARCHAR )'),
      'ZCOREUSER': (
          'CREATE TABLE ZCOREUSER ( Z_PK INTEGER PRIMARY KEY, Z_ENT INTEGER, '
          'Z_OPT INTEGER, ZDSID INTEGER, ZISFAMILYORGANIZER INTEGER, '
          'ZISPARENT INTEGER, ZPASSCODEENTRYATTEMPTCOUNT INTEGER, '
          'ZPASSCODERECOVERYATTEMPTCOUNT INTEGER, ZSUPPORTSENCRYPTION INTEGER, '
          'ZCLOUDSETTINGS INTEGER, ZFAMILYSETTINGS INTEGER, '
          'ZLOCALSETTINGS INTEGER, ZLOCALUSERDEVICESTATE INTEGER, '
          'ZPASSCODEENTRYTIMEOUTENDDATE TIMESTAMP, ZALTDSID VARCHAR, '
          'ZAPPLEID VARCHAR, ZFAMILYMEMBERTYPE VARCHAR, ZFAMILYNAME VARCHAR, '
          'ZGIVENNAME VARCHAR, ZPHONETICFAMILYNAME VARCHAR, '
          'ZPHONETICGIVENNAME VARCHAR )')}

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
  def ParseScreenTimeRow(self, parser_mediator, query, row, **unused_kwargs):
    """Parses a Screen Time row.

    Args:
      parser_mediator (ParserMediator): mediates interactions between parsers
          and other components, such as storage and dfVFS.
      query (str): query that created the row.
      row (sqlite3.Row): row.
    """
    query_hash = hash(query)

    event_data = IOSScreenTimeEventData()
    event_data.bundle_identifier = self._GetRowValue(
        query_hash, row, 'ZBUNDLEIDENTIFIER')
    event_data.device_identifier = self._GetRowValue(
        query_hash, row, 'ZIDENTIFIER')
    event_data.device_name = self._GetRowValue(query_hash, row, 'ZNAME')
    event_data.domain = self._GetRowValue(query_hash, row, 'ZDOMAIN')
    event_data.start_time = self._GetDateTimeRowValue(
        query_hash, row, 'ZSTARTDATE')
    event_data.total_time = self._GetRowValue(
        query_hash, row, 'ZTOTALTIMEINSECONDS')
    event_data.user_family_name = self._GetRowValue(
        query_hash, row, 'ZFAMILYNAME')
    event_data.user_given_name = self._GetRowValue(
        query_hash, row, 'ZGIVENNAME')

    parser_mediator.ProduceEventData(event_data)


sqlite.SQLiteParser.RegisterPlugin(IOSScreenTimePlugin)
