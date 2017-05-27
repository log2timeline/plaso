# -*- coding: utf-8 -*-
"""This file contains a parser for the Kik database on iOS.

Kik messages on iOS devices are stored in an
SQLite database file named kik.sqlite.
"""

from dfdatetime import cocoa_time as dfdatetime_cocoa_time

from plaso.containers import events
from plaso.containers import time_events
from plaso.lib import definitions
from plaso.parsers import sqlite
from plaso.parsers.sqlite_plugins import interface


class KikIOSMessageEventData(events.EventData):
  """Kik message event data.

  Args:
    body (str): content of the message.
    message_status (str): message status, such as:
        read, unread, not sent, delivered, etc.
    message_type (str): message type, either Sent or Received.
    username (str): unique username of the sender or receiver.
  """

  DATA_TYPE = u'ios:kik:messaging'

  def __init__(self):
    """Initializes event data."""
    super(KikIOSMessageEventData, self).__init__(data_type=self.DATA_TYPE)
    self.body = None
    self.displayname = None
    self.message_status = None
    self.message_type = None
    self.username = None


class KikIOSPlugin(interface.SQLitePlugin):
  """SQLite plugin for Kik iOS database."""

  NAME = u'kik_messenger'
  DESCRIPTION = u'Parser for iOS Kik messenger SQLite database files.'

  # Define the needed queries.
  QUERIES = [
      (u'SELECT a.Z_PK AS id, b.ZUSERNAME, b.ZDISPLAYNAME,'
       u'a.ZRECEIVEDTIMESTAMP, a.ZSTATE, a.ZTYPE, a.ZBODY '
       u'FROM ZKIKMESSAGE a JOIN ZKIKUSER b ON b.ZEXTRA = a.ZUSER',
       u'ParseMessageRow')]

  # The required tables.
  REQUIRED_TABLES = frozenset([u'ZKIKMESSAGE', u'ZKIKUSER'])

  SCHEMAS = [{
      u'Z_3MESSAGES': (
          u'CREATE TABLE Z_3MESSAGES ( Z_3CHAT INTEGER, Z_5MESSAGES INTEGER, '
          u'PRIMARY KEY (Z_3CHAT, Z_5MESSAGES) )'),
      u'Z_6ADMINSINVERSE': (
          u'CREATE TABLE Z_6ADMINSINVERSE ( Z_6ADMINS INTEGER, '
          u'Z_6ADMINSINVERSE INTEGER, PRIMARY KEY (Z_6ADMINS, '
          u'Z_6ADMINSINVERSE) )'),
      u'Z_6BANSINVERSE': (
          u'CREATE TABLE Z_6BANSINVERSE ( Z_6BANS INTEGER, Z_6BANSINVERSE '
          u'INTEGER, PRIMARY KEY (Z_6BANS, Z_6BANSINVERSE) )'),
      u'Z_6MEMBERS': (
          u'CREATE TABLE Z_6MEMBERS ( Z_6MEMBERSINVERSE INTEGER, Z_6MEMBERS '
          u'INTEGER, PRIMARY KEY (Z_6MEMBERSINVERSE, Z_6MEMBERS) )'),
      u'Z_METADATA': (
          u'CREATE TABLE Z_METADATA (Z_VERSION INTEGER PRIMARY KEY, Z_UUID '
          u'VARCHAR(255), Z_PLIST BLOB)'),
      u'Z_PRIMARYKEY': (
          u'CREATE TABLE Z_PRIMARYKEY (Z_ENT INTEGER PRIMARY KEY, Z_NAME '
          u'VARCHAR, Z_SUPER INTEGER, Z_MAX INTEGER)'),
      u'ZKIKATTACHMENT': (
          u'CREATE TABLE ZKIKATTACHMENT ( Z_PK INTEGER PRIMARY KEY, Z_ENT '
          u'INTEGER, Z_OPT INTEGER, ZFLAGS INTEGER, ZINTERNALID INTEGER, '
          u'ZRETRYCOUNT INTEGER, ZSTATE INTEGER, ZTYPE INTEGER, ZEXTRA '
          u'INTEGER, ZMESSAGE INTEGER, ZLASTACCESSTIMESTAMP TIMESTAMP, '
          u'ZTIMESTAMP TIMESTAMP, ZCONTENT VARCHAR )'),
      u'ZKIKATTACHMENTEXTRA': (
          u'CREATE TABLE ZKIKATTACHMENTEXTRA ( Z_PK INTEGER PRIMARY KEY, Z_ENT '
          u'INTEGER, Z_OPT INTEGER, ZATTACHMENT INTEGER, ZENCRYPTIONKEY '
          u'BLOB )'),
      u'ZKIKCHAT': (
          u'CREATE TABLE ZKIKCHAT ( Z_PK INTEGER PRIMARY KEY, Z_ENT INTEGER, '
          u'Z_OPT INTEGER, ZFLAGS INTEGER, ZDRAFTMESSAGE INTEGER, ZEXTRA '
          u'INTEGER, ZLASTMESSAGE INTEGER, ZUSER INTEGER, ZDATEUPDATED '
          u'TIMESTAMP )'),
      u'ZKIKCHATEXTRA': (
          u'CREATE TABLE ZKIKCHATEXTRA ( Z_PK INTEGER PRIMARY KEY, Z_ENT '
          u'INTEGER, Z_OPT INTEGER, ZCHAT INTEGER, ZLASTSEENMESSAGE INTEGER, '
          u'ZMUTEDTIMESTAMP TIMESTAMP )'),
      u'ZKIKMESSAGE': (
          u'CREATE TABLE ZKIKMESSAGE ( Z_PK INTEGER PRIMARY KEY, Z_ENT '
          u'INTEGER, Z_OPT INTEGER, ZFLAGS INTEGER, ZINTERNALID INTEGER, '
          u'ZSTATE INTEGER, ZSYSTEMSTATE INTEGER, ZTYPE INTEGER, ZCHATEXTRA '
          u'INTEGER, ZDRAFTMESSAGECHAT INTEGER, ZLASTMESSAGECHAT INTEGER, '
          u'ZLASTMESSAGEUSER INTEGER, ZUSER INTEGER, ZRECEIVEDTIMESTAMP '
          u'TIMESTAMP, ZTIMESTAMP TIMESTAMP, ZBODY VARCHAR, ZSTANZAID VARCHAR, '
          u'ZRENDERINSTRUCTIONSET BLOB )'),
      u'ZKIKUSER': (
          u'CREATE TABLE ZKIKUSER ( Z_PK INTEGER PRIMARY KEY, Z_ENT INTEGER, '
          u'Z_OPT INTEGER, ZADDRESSBOOKID INTEGER, ZFLAGS INTEGER, ZINTERNALID '
          u'INTEGER, ZPRESENCE INTEGER, ZTYPE INTEGER, ZCHATUSER INTEGER, '
          u'ZEXTRA INTEGER, ZLASTMESSAGE INTEGER, ZDISPLAYNAME VARCHAR, '
          u'ZDISPLAYNAMEASCII VARCHAR, ZEMAIL VARCHAR, ZFIRSTNAME VARCHAR, '
          u'ZGROUPTAG VARCHAR, ZJID VARCHAR, ZLASTNAME VARCHAR, ZPPTIMESTAMP '
          u'VARCHAR, ZPPURL VARCHAR, ZSTATUS VARCHAR, ZUSERNAME VARCHAR, '
          u'ZCONTENTLINKSPROTODATA BLOB )'),
      u'ZKIKUSEREXTRA': (
          u'CREATE TABLE ZKIKUSEREXTRA ( Z_PK INTEGER PRIMARY KEY, Z_ENT '
          u'INTEGER, Z_OPT INTEGER, ZLOCALFLAGS INTEGER, ZUSER INTEGER, '
          u'ZPUBLICMESSAGINGKEY BLOB )')}]

  def ParseMessageRow(self, parser_mediator, row, query=None, **unused_kwargs):
    """Parses a message row.

    Args:
      parser_mediator (ParserMediator): mediates interactions between parsers
          and other components, such as storage and dfvfs.
      row (sqlite3.Row): row.
      query (Optional[str]): query.
    """
    # Note that pysqlite does not accept a Unicode string in row['string'] and
    # will raise "IndexError: Index must be int or string".

    event_data = KikIOSMessageEventData()
    event_data.body = row['ZBODY']
    event_data.displayname = row['ZDISPLAYNAME']
    event_data.message_status = row['ZSTATE']
    event_data.message_type = row['ZTYPE']
    event_data.offset = row['id']
    event_data.query = query
    event_data.username = row['ZUSERNAME']

    # Convert the floating point value to an integer.
    timestamp = int(row['ZRECEIVEDTIMESTAMP'])
    date_time = dfdatetime_cocoa_time.CocoaTime(timestamp=timestamp)
    event = time_events.DateTimeValuesEvent(
        date_time, definitions.TIME_DESCRIPTION_CREATION)
    parser_mediator.ProduceEventWithEventData(event, event_data)


sqlite.SQLiteParser.RegisterPlugin(KikIOSPlugin)
