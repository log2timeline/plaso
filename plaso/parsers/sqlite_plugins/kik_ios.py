# -*- coding: utf-8 -*-
"""This file contains a parser for the Kik database on iOS.

Kik messages on iOS devices are stored in an
SQLite database file named kik.sqlite.
"""

from plaso.containers import time_events
from plaso.lib import eventdata
from plaso.parsers import sqlite
from plaso.parsers.sqlite_plugins import interface


class KikIOSMessageEvent(time_events.CocoaTimeEvent):
  """Convenience class for a Kik message event."""

  DATA_TYPE = u'ios:kik:messaging'

  def __init__(
      self, cocoa_time, identifier, username, displayname,
      message_status, message_type, body):
    """Initializes the event object.

    Args:
      cocoa_time: The Cocoa time value.
      identifier: The row identifier.
      username: The unique username of the sender/receiver.
      message_status:  Read, unread, not sent, delivered, etc.
      message_type: Sent or Received.
      body: Content of the message.
    """
    super(KikIOSMessageEvent, self).__init__(
        cocoa_time, eventdata.EventTimestamp.CREATION_TIME)
    self.offset = identifier
    self.username = username
    self.displayname = displayname
    self.message_status = message_status
    self.message_type = message_type
    self.body = body


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

  SCHEMAS = [
      {u'Z_3MESSAGES':
          u'CREATE TABLE Z_3MESSAGES ( Z_3CHAT INTEGER, Z_5MESSAGES INTEGER, '
          u'PRIMARY KEY (Z_3CHAT, Z_5MESSAGES) )',
      u'Z_6ADMINSINVERSE':
          u'CREATE TABLE Z_6ADMINSINVERSE ( Z_6ADMINS INTEGER, '
          u'Z_6ADMINSINVERSE INTEGER, PRIMARY KEY (Z_6ADMINS, '
          u'Z_6ADMINSINVERSE) )',
      u'Z_6BANSINVERSE':
          u'CREATE TABLE Z_6BANSINVERSE ( Z_6BANS INTEGER, Z_6BANSINVERSE '
          u'INTEGER, PRIMARY KEY (Z_6BANS, Z_6BANSINVERSE) )',
      u'Z_6MEMBERS':
          u'CREATE TABLE Z_6MEMBERS ( Z_6MEMBERSINVERSE INTEGER, Z_6MEMBERS '
          u'INTEGER, PRIMARY KEY (Z_6MEMBERSINVERSE, Z_6MEMBERS) )',
      u'Z_METADATA':
          u'CREATE TABLE Z_METADATA (Z_VERSION INTEGER PRIMARY KEY, Z_UUID '
          u'VARCHAR(255), Z_PLIST BLOB)',
      u'Z_PRIMARYKEY':
          u'CREATE TABLE Z_PRIMARYKEY (Z_ENT INTEGER PRIMARY KEY, Z_NAME '
          u'VARCHAR, Z_SUPER INTEGER, Z_MAX INTEGER)',
      u'ZKIKATTACHMENT':
          u'CREATE TABLE ZKIKATTACHMENT ( Z_PK INTEGER PRIMARY KEY, Z_ENT '
          u'INTEGER, Z_OPT INTEGER, ZFLAGS INTEGER, ZINTERNALID INTEGER, '
          u'ZRETRYCOUNT INTEGER, ZSTATE INTEGER, ZTYPE INTEGER, ZEXTRA '
          u'INTEGER, ZMESSAGE INTEGER, ZLASTACCESSTIMESTAMP TIMESTAMP, '
          u'ZTIMESTAMP TIMESTAMP, ZCONTENT VARCHAR )',
      u'ZKIKATTACHMENTEXTRA':
          u'CREATE TABLE ZKIKATTACHMENTEXTRA ( Z_PK INTEGER PRIMARY KEY, '
          u'Z_ENT INTEGER, Z_OPT INTEGER, ZATTACHMENT INTEGER, ZENCRYPTIONKEY '
          u'BLOB )',
      u'ZKIKCHAT':
          u'CREATE TABLE ZKIKCHAT ( Z_PK INTEGER PRIMARY KEY, Z_ENT INTEGER, '
          u'Z_OPT INTEGER, ZFLAGS INTEGER, ZDRAFTMESSAGE INTEGER, ZEXTRA '
          u'INTEGER, ZLASTMESSAGE INTEGER, ZUSER INTEGER, ZDATEUPDATED '
          u'TIMESTAMP )',
      u'ZKIKCHATEXTRA':
          u'CREATE TABLE ZKIKCHATEXTRA ( Z_PK INTEGER PRIMARY KEY, Z_ENT '
          u'INTEGER, Z_OPT INTEGER, ZCHAT INTEGER, ZLASTSEENMESSAGE INTEGER, '
          u'ZMUTEDTIMESTAMP TIMESTAMP )',
      u'ZKIKMESSAGE':
          u'CREATE TABLE ZKIKMESSAGE ( Z_PK INTEGER PRIMARY KEY, Z_ENT '
          u'INTEGER, Z_OPT INTEGER, ZFLAGS INTEGER, ZINTERNALID INTEGER, '
          u'ZSTATE INTEGER, ZSYSTEMSTATE INTEGER, ZTYPE INTEGER, ZCHATEXTRA '
          u'INTEGER, ZDRAFTMESSAGECHAT INTEGER, ZLASTMESSAGECHAT INTEGER, '
          u'ZLASTMESSAGEUSER INTEGER, ZUSER INTEGER, ZRECEIVEDTIMESTAMP '
          u'TIMESTAMP, ZTIMESTAMP TIMESTAMP, ZBODY VARCHAR, ZSTANZAID '
          u'VARCHAR, ZRENDERINSTRUCTIONSET BLOB )',
      u'ZKIKUSER':
          u'CREATE TABLE ZKIKUSER ( Z_PK INTEGER PRIMARY KEY, Z_ENT INTEGER, '
          u'Z_OPT INTEGER, ZADDRESSBOOKID INTEGER, ZFLAGS INTEGER, '
          u'ZINTERNALID INTEGER, ZPRESENCE INTEGER, ZTYPE INTEGER, ZCHATUSER '
          u'INTEGER, ZEXTRA INTEGER, ZLASTMESSAGE INTEGER, ZDISPLAYNAME '
          u'VARCHAR, ZDISPLAYNAMEASCII VARCHAR, ZEMAIL VARCHAR, ZFIRSTNAME '
          u'VARCHAR, ZGROUPTAG VARCHAR, ZJID VARCHAR, ZLASTNAME VARCHAR, '
          u'ZPPTIMESTAMP VARCHAR, ZPPURL VARCHAR, ZSTATUS VARCHAR, ZUSERNAME '
          u'VARCHAR, ZCONTENTLINKSPROTODATA BLOB )',
      u'ZKIKUSEREXTRA':
          u'CREATE TABLE ZKIKUSEREXTRA ( Z_PK INTEGER PRIMARY KEY, Z_ENT '
          u'INTEGER, Z_OPT INTEGER, ZLOCALFLAGS INTEGER, ZUSER INTEGER, '
          u'ZPUBLICMESSAGINGKEY BLOB )'}]

  def ParseMessageRow(self, parser_mediator, row, query=None, **unused_kwargs):
    """Parses a message row.

    Args:
      parser_mediator (ParserMediator): parser mediator.
      row (sqlite3.Row): row resulting from the query.
      query (Optional[str]): query string.
    """
    # Note that pysqlite does not accept a Unicode string in row['string'] and
    # will raise "IndexError: Index must be int or string".

    event_object = KikIOSMessageEvent(
        row['ZRECEIVEDTIMESTAMP'], row['id'], row['ZUSERNAME'],
        row['ZDISPLAYNAME'], row['ZSTATE'], row['ZTYPE'], row['ZBODY'])
    parser_mediator.ProduceEvent(event_object, query=query)

sqlite.SQLiteParser.RegisterPlugin(KikIOSPlugin)
