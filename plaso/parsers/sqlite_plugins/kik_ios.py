# -*- coding: utf-8 -*-
"""This file contains a parser for the Kik database on iOS.

Kik messages on iOS devices are stored in an
SQLite database file named kik.sqlite.
"""

from __future__ import unicode_literals

from dfdatetime import cocoa_time as dfdatetime_cocoa_time

from plaso.containers import events
from plaso.containers import time_events
from plaso.lib import definitions
from plaso.parsers import sqlite
from plaso.parsers.sqlite_plugins import interface


class KikIOSMessageEventData(events.EventData):
  """Kik message event data.

  Attributes:
    body (str): content of the message.
    message_status (str): message status, such as:
        read, unread, not sent, delivered, etc.
    message_type (str): message type, either Sent or Received.
    username (str): unique username of the sender or receiver.
  """

  DATA_TYPE = 'ios:kik:messaging'

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

  NAME = 'kik_messenger'
  DESCRIPTION = 'Parser for iOS Kik messenger SQLite database files.'

  REQUIRED_STRUCTURE = {
      'ZKIKMESSAGE': frozenset([
          'Z_PK', 'ZRECEIVEDTIMESTAMP', 'ZSTATE', 'ZTYPE', 'ZBODY', 'ZUSER']),
      'ZKIKUSER': frozenset([
          'ZUSERNAME', 'ZDISPLAYNAME', 'ZEXTRA'])}

  QUERIES = [
      ('SELECT a.Z_PK AS id, b.ZUSERNAME, b.ZDISPLAYNAME,'
       'a.ZRECEIVEDTIMESTAMP, a.ZSTATE, a.ZTYPE, a.ZBODY '
       'FROM ZKIKMESSAGE a JOIN ZKIKUSER b ON b.ZEXTRA = a.ZUSER',
       'ParseMessageRow')]

  SCHEMAS = [{
      'Z_3MESSAGES': (
          'CREATE TABLE Z_3MESSAGES ( Z_3CHAT INTEGER, Z_5MESSAGES INTEGER, '
          'PRIMARY KEY (Z_3CHAT, Z_5MESSAGES) )'),
      'Z_6ADMINSINVERSE': (
          'CREATE TABLE Z_6ADMINSINVERSE ( Z_6ADMINS INTEGER, '
          'Z_6ADMINSINVERSE INTEGER, PRIMARY KEY (Z_6ADMINS, '
          'Z_6ADMINSINVERSE) )'),
      'Z_6BANSINVERSE': (
          'CREATE TABLE Z_6BANSINVERSE ( Z_6BANS INTEGER, Z_6BANSINVERSE '
          'INTEGER, PRIMARY KEY (Z_6BANS, Z_6BANSINVERSE) )'),
      'Z_6MEMBERS': (
          'CREATE TABLE Z_6MEMBERS ( Z_6MEMBERSINVERSE INTEGER, Z_6MEMBERS '
          'INTEGER, PRIMARY KEY (Z_6MEMBERSINVERSE, Z_6MEMBERS) )'),
      'Z_METADATA': (
          'CREATE TABLE Z_METADATA (Z_VERSION INTEGER PRIMARY KEY, Z_UUID '
          'VARCHAR(255), Z_PLIST BLOB)'),
      'Z_PRIMARYKEY': (
          'CREATE TABLE Z_PRIMARYKEY (Z_ENT INTEGER PRIMARY KEY, Z_NAME '
          'VARCHAR, Z_SUPER INTEGER, Z_MAX INTEGER)'),
      'ZKIKATTACHMENT': (
          'CREATE TABLE ZKIKATTACHMENT ( Z_PK INTEGER PRIMARY KEY, Z_ENT '
          'INTEGER, Z_OPT INTEGER, ZFLAGS INTEGER, ZINTERNALID INTEGER, '
          'ZRETRYCOUNT INTEGER, ZSTATE INTEGER, ZTYPE INTEGER, ZEXTRA '
          'INTEGER, ZMESSAGE INTEGER, ZLASTACCESSTIMESTAMP TIMESTAMP, '
          'ZTIMESTAMP TIMESTAMP, ZCONTENT VARCHAR )'),
      'ZKIKATTACHMENTEXTRA': (
          'CREATE TABLE ZKIKATTACHMENTEXTRA ( Z_PK INTEGER PRIMARY KEY, Z_ENT '
          'INTEGER, Z_OPT INTEGER, ZATTACHMENT INTEGER, ZENCRYPTIONKEY '
          'BLOB )'),
      'ZKIKCHAT': (
          'CREATE TABLE ZKIKCHAT ( Z_PK INTEGER PRIMARY KEY, Z_ENT INTEGER, '
          'Z_OPT INTEGER, ZFLAGS INTEGER, ZDRAFTMESSAGE INTEGER, ZEXTRA '
          'INTEGER, ZLASTMESSAGE INTEGER, ZUSER INTEGER, ZDATEUPDATED '
          'TIMESTAMP )'),
      'ZKIKCHATEXTRA': (
          'CREATE TABLE ZKIKCHATEXTRA ( Z_PK INTEGER PRIMARY KEY, Z_ENT '
          'INTEGER, Z_OPT INTEGER, ZCHAT INTEGER, ZLASTSEENMESSAGE INTEGER, '
          'ZMUTEDTIMESTAMP TIMESTAMP )'),
      'ZKIKMESSAGE': (
          'CREATE TABLE ZKIKMESSAGE ( Z_PK INTEGER PRIMARY KEY, Z_ENT '
          'INTEGER, Z_OPT INTEGER, ZFLAGS INTEGER, ZINTERNALID INTEGER, '
          'ZSTATE INTEGER, ZSYSTEMSTATE INTEGER, ZTYPE INTEGER, ZCHATEXTRA '
          'INTEGER, ZDRAFTMESSAGECHAT INTEGER, ZLASTMESSAGECHAT INTEGER, '
          'ZLASTMESSAGEUSER INTEGER, ZUSER INTEGER, ZRECEIVEDTIMESTAMP '
          'TIMESTAMP, ZTIMESTAMP TIMESTAMP, ZBODY VARCHAR, ZSTANZAID VARCHAR, '
          'ZRENDERINSTRUCTIONSET BLOB )'),
      'ZKIKUSER': (
          'CREATE TABLE ZKIKUSER ( Z_PK INTEGER PRIMARY KEY, Z_ENT INTEGER, '
          'Z_OPT INTEGER, ZADDRESSBOOKID INTEGER, ZFLAGS INTEGER, ZINTERNALID '
          'INTEGER, ZPRESENCE INTEGER, ZTYPE INTEGER, ZCHATUSER INTEGER, '
          'ZEXTRA INTEGER, ZLASTMESSAGE INTEGER, ZDISPLAYNAME VARCHAR, '
          'ZDISPLAYNAMEASCII VARCHAR, ZEMAIL VARCHAR, ZFIRSTNAME VARCHAR, '
          'ZGROUPTAG VARCHAR, ZJID VARCHAR, ZLASTNAME VARCHAR, ZPPTIMESTAMP '
          'VARCHAR, ZPPURL VARCHAR, ZSTATUS VARCHAR, ZUSERNAME VARCHAR, '
          'ZCONTENTLINKSPROTODATA BLOB )'),
      'ZKIKUSEREXTRA': (
          'CREATE TABLE ZKIKUSEREXTRA ( Z_PK INTEGER PRIMARY KEY, Z_ENT '
          'INTEGER, Z_OPT INTEGER, ZLOCALFLAGS INTEGER, ZUSER INTEGER, '
          'ZPUBLICMESSAGINGKEY BLOB )')}]

  def ParseMessageRow(self, parser_mediator, query, row, **unused_kwargs):
    """Parses a message row.

    Args:
      parser_mediator (ParserMediator): mediates interactions between parsers
          and other components, such as storage and dfvfs.
      query (str): query that created the row.
      row (sqlite3.Row): row.
    """
    query_hash = hash(query)

    event_data = KikIOSMessageEventData()
    event_data.body = self._GetRowValue(query_hash, row, 'ZBODY')
    event_data.displayname = self._GetRowValue(query_hash, row, 'ZDISPLAYNAME')
    event_data.message_status = self._GetRowValue(query_hash, row, 'ZSTATE')
    event_data.message_type = self._GetRowValue(query_hash, row, 'ZTYPE')
    event_data.offset = self._GetRowValue(query_hash, row, 'id')
    event_data.query = query
    event_data.username = self._GetRowValue(query_hash, row, 'ZUSERNAME')

    timestamp = self._GetRowValue(query_hash, row, 'ZRECEIVEDTIMESTAMP')
    # Convert the floating point value to an integer.
    timestamp = int(timestamp)
    date_time = dfdatetime_cocoa_time.CocoaTime(timestamp=timestamp)
    event = time_events.DateTimeValuesEvent(
        date_time, definitions.TIME_DESCRIPTION_CREATION)
    parser_mediator.ProduceEventWithEventData(event, event_data)


sqlite.SQLiteParser.RegisterPlugin(KikIOSPlugin)
