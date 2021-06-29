# -*- coding: utf-8 -*-
"""SQLite parser plugin for MacOS and iOS iMessage database files."""

from dfdatetime import cocoa_time as dfdatetime_cocoa_time

from plaso.containers import events
from plaso.containers import time_events
from plaso.lib import definitions
from plaso.parsers import sqlite
from plaso.parsers.sqlite_plugins import interface


class IMessageEventData(events.EventData):
  """iMessage and SMS event data.

  Attributes:
    attachment_location (str): location of the attachment.
    imessage_id (str): mobile number or email address the message was sent
        to or received from.
    message_type (int): value to indicate the message was sent (1) or
        received (0).
    offset (str): identifier of the row, from which the event data was
        extracted.
    query (str): SQL query that was used to obtain the event data.
    read_receipt (bool): True if the message read receipt was received.
    service (str): service, which is either SMS or iMessage.
    text (str): content of the message.
  """

  DATA_TYPE = 'imessage:event:chat'

  def __init__(self):
    """Initializes event data."""
    super(IMessageEventData, self).__init__(data_type=self.DATA_TYPE)
    self.attachment_location = None
    self.imessage_id = None
    self.message_type = None
    self.offset = None
    self.query = None
    self.read_receipt = None
    self.service = None
    self.text = None


class IMessagePlugin(interface.SQLitePlugin):
  """SQLite parser plugin for MacOS and iOS iMessage database files.

  The iMessage database file is typically stored in:
  chat.db
  sms.db
  """

  NAME = 'imessage'
  DATA_FORMAT = 'MacOS and iOS iMessage database (chat.db, sms.db) file'

  REQUIRED_STRUCTURE = {
      'message': frozenset([
          'date', 'ROWID', 'is_read', 'is_from_me', 'service', 'text',
          'handle_id']),
      'handle': frozenset([
          'id', 'ROWID']),
      'attachment': frozenset([
          'filename', 'ROWID']),
      'message_attachment_join': frozenset([
          'message_id', 'attachment_id'])}

  QUERIES = [
      ('SELECT m.date, m.ROWID, h.id AS imessage_id, m.is_read AS '
       'read_receipt, m.is_from_me AS message_type, m.service, a.filename AS'
       '"attachment_location", m.text FROM message AS m JOIN handle AS h ON '
       'h.ROWID = m.handle_id LEFT OUTER JOIN message_attachment_join AS maj '
       'ON m.ROWID = maj.message_id LEFT OUTER JOIN attachment AS a ON '
       'maj.attachment_id = a.ROWID', 'ParseMessageRow')]

  SCHEMAS = [{
      '_SqliteDatabaseProperties': (
          'CREATE TABLE _SqliteDatabaseProperties (key TEXT, value TEXT, '
          'UNIQUE(key))'),
      'attachment': (
          'CREATE TABLE attachment (ROWID INTEGER PRIMARY KEY AUTOINCREMENT, '
          'guid TEXT UNIQUE NOT NULL, created_date INTEGER DEFAULT 0, '
          'start_date INTEGER DEFAULT 0, filename TEXT, uti TEXT, mime_type '
          'TEXT, transfer_state INTEGER DEFAULT 0, is_outgoing INTEGER '
          'DEFAULT 0, user_info BLOB, transfer_name TEXT, total_bytes INTEGER '
          'DEFAULT 0)'),
      'chat': (
          'CREATE TABLE chat (ROWID INTEGER PRIMARY KEY AUTOINCREMENT, guid '
          'TEXT UNIQUE NOT NULL, style INTEGER, state INTEGER, account_id '
          'TEXT, properties BLOB, chat_identifier TEXT, service_name TEXT, '
          'room_name TEXT, account_login TEXT, is_archived INTEGER DEFAULT 0, '
          'last_addressed_handle TEXT, display_name TEXT, group_id TEXT, '
          'is_filtered INTEGER, successful_query INTEGER)'),
      'chat_handle_join': (
          'CREATE TABLE chat_handle_join (chat_id INTEGER REFERENCES chat '
          '(ROWID) ON DELETE CASCADE, handle_id INTEGER REFERENCES handle '
          '(ROWID) ON DELETE CASCADE, UNIQUE(chat_id, handle_id))'),
      'chat_message_join': (
          'CREATE TABLE chat_message_join (chat_id INTEGER REFERENCES chat '
          '(ROWID) ON DELETE CASCADE, message_id INTEGER REFERENCES message '
          '(ROWID) ON DELETE CASCADE, PRIMARY KEY (chat_id, message_id))'),
      'deleted_messages': (
          'CREATE TABLE deleted_messages (ROWID INTEGER PRIMARY KEY '
          'AUTOINCREMENT UNIQUE, guid TEXT NOT NULL)'),
      'handle': (
          'CREATE TABLE handle (ROWID INTEGER PRIMARY KEY AUTOINCREMENT '
          'UNIQUE, id TEXT NOT NULL, country TEXT, service TEXT NOT NULL, '
          'uncanonicalized_id TEXT, UNIQUE (id, service) )'),
      'message': (
          'CREATE TABLE message (ROWID INTEGER PRIMARY KEY AUTOINCREMENT, '
          'guid TEXT UNIQUE NOT NULL, text TEXT, replace INTEGER DEFAULT 0, '
          'service_center TEXT, handle_id INTEGER DEFAULT 0, subject TEXT, '
          'country TEXT, attributedBody BLOB, version INTEGER DEFAULT 0, type '
          'INTEGER DEFAULT 0, service TEXT, account TEXT, account_guid TEXT, '
          'error INTEGER DEFAULT 0, date INTEGER, date_read INTEGER, '
          'date_delivered INTEGER, is_delivered INTEGER DEFAULT 0, '
          'is_finished INTEGER DEFAULT 0, is_emote INTEGER DEFAULT 0, '
          'is_from_me INTEGER DEFAULT 0, is_empty INTEGER DEFAULT 0, '
          'is_delayed INTEGER DEFAULT 0, is_auto_reply INTEGER DEFAULT 0, '
          'is_prepared INTEGER DEFAULT 0, is_read INTEGER DEFAULT 0, '
          'is_system_message INTEGER DEFAULT 0, is_sent INTEGER DEFAULT 0, '
          'has_dd_results INTEGER DEFAULT 0, is_service_message INTEGER '
          'DEFAULT 0, is_forward INTEGER DEFAULT 0, was_downgraded INTEGER '
          'DEFAULT 0, is_archive INTEGER DEFAULT 0, cache_has_attachments '
          'INTEGER DEFAULT 0, cache_roomnames TEXT, was_data_detected INTEGER '
          'DEFAULT 0, was_deduplicated INTEGER DEFAULT 0, is_audio_message '
          'INTEGER DEFAULT 0, is_played INTEGER DEFAULT 0, date_played '
          'INTEGER, item_type INTEGER DEFAULT 0, other_handle INTEGER DEFAULT '
          '0, group_title TEXT, group_action_type INTEGER DEFAULT 0, '
          'share_status INTEGER DEFAULT 0, share_direction INTEGER DEFAULT 0, '
          'is_expirable INTEGER DEFAULT 0, expire_state INTEGER DEFAULT 0, '
          'message_action_type INTEGER DEFAULT 0, message_source INTEGER '
          'DEFAULT 0)'),
      'message_attachment_join': (
          'CREATE TABLE message_attachment_join (message_id INTEGER '
          'REFERENCES message (ROWID) ON DELETE CASCADE, attachment_id '
          'INTEGER REFERENCES attachment (ROWID) ON DELETE CASCADE, '
          'UNIQUE(message_id, attachment_id))')}]

  def ParseMessageRow(self, parser_mediator, query, row, **unused_kwargs):
    """Parses a message row.

    Args:
      parser_mediator (ParserMediator): mediates interactions between parsers
          and other components, such as storage and dfvfs.
      query (str): query that created the row.
      row (sqlite3.Row): row.
    """
    query_hash = hash(query)

    event_data = IMessageEventData()
    event_data.attachment_location = self._GetRowValue(
        query_hash, row, 'attachment_location')
    event_data.imessage_id = self._GetRowValue(query_hash, row, 'imessage_id')
    event_data.message_type = self._GetRowValue(query_hash, row, 'message_type')
    event_data.offset = self._GetRowValue(query_hash, row, 'ROWID')
    event_data.query = query
    event_data.read_receipt = self._GetRowValue(query_hash, row, 'read_receipt')
    event_data.service = self._GetRowValue(query_hash, row, 'service')
    event_data.text = self._GetRowValue(query_hash, row, 'text')

    timestamp = self._GetRowValue(query_hash, row, 'date')
    date_time = dfdatetime_cocoa_time.CocoaTime(timestamp=timestamp)
    event = time_events.DateTimeValuesEvent(
        date_time, definitions.TIME_DESCRIPTION_CREATION)
    parser_mediator.ProduceEventWithEventData(event, event_data)


sqlite.SQLiteParser.RegisterPlugin(IMessagePlugin)
