# -*- coding: utf-8 -*-
"""This file contains a parser for the iMessage database on OSX and iOS.

iMessage and SMS data in OSX and iOS are stored in SQLite databases named
chat.db and sms.db respectively.
"""

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
    read_receipt (bool): True if the message read receipt was received.
    service (str): service, which is either SMS or iMessage.
    text (str): content of the message.
  """

  DATA_TYPE = u'imessage:event:chat'

  def __init__(self):
    """Initializes event data."""
    super(IMessageEventData, self).__init__(data_type=self.DATA_TYPE)
    self.attachment_location = None
    self.imessage_id = None
    self.message_type = None
    self.read_receipt = None
    self.service = None
    self.text = None


class IMessagePlugin(interface.SQLitePlugin):
  """SQLite plugin for the iMessage and SMS database."""

  NAME = u'imessage'
  DESCRIPTION = u'Parser for the iMessage and SMS SQLite databases on OSX and '\
                u'iOS.'

  # Define the needed queries.
  QUERIES = [
      (u'SELECT m.date, m.ROWID, h.id AS imessage_id, m.is_read AS '
       u'read_receipt, m.is_from_me AS message_type, m.service, a.filename AS'
       u'"attachment_location", m.text FROM message AS m JOIN handle AS h ON '
       u'h.ROWID = m.handle_id LEFT OUTER JOIN message_attachment_join AS maj '
       u'ON m.ROWID = maj.message_id LEFT OUTER JOIN attachment AS a ON '
       u'maj.attachment_id = a.ROWID', u'ParseMessageRow')]

  # The required tables.
  REQUIRED_TABLES = frozenset([
      u'message', u'handle', u'attachment', u'message_attachment_join'])

  SCHEMAS = [{
      u'_SqliteDatabaseProperties': (
          u'CREATE TABLE _SqliteDatabaseProperties (key TEXT, value TEXT, '
          u'UNIQUE(key))'),
      u'attachment': (
          u'CREATE TABLE attachment (ROWID INTEGER PRIMARY KEY AUTOINCREMENT, '
          u'guid TEXT UNIQUE NOT NULL, created_date INTEGER DEFAULT 0, '
          u'start_date INTEGER DEFAULT 0, filename TEXT, uti TEXT, mime_type '
          u'TEXT, transfer_state INTEGER DEFAULT 0, is_outgoing INTEGER '
          u'DEFAULT 0, user_info BLOB, transfer_name TEXT, total_bytes INTEGER '
          u'DEFAULT 0)'),
      u'chat': (
          u'CREATE TABLE chat (ROWID INTEGER PRIMARY KEY AUTOINCREMENT, guid '
          u'TEXT UNIQUE NOT NULL, style INTEGER, state INTEGER, account_id '
          u'TEXT, properties BLOB, chat_identifier TEXT, service_name TEXT, '
          u'room_name TEXT, account_login TEXT, is_archived INTEGER DEFAULT 0, '
          u'last_addressed_handle TEXT, display_name TEXT, group_id TEXT, '
          u'is_filtered INTEGER, successful_query INTEGER)'),
      u'chat_handle_join': (
          u'CREATE TABLE chat_handle_join (chat_id INTEGER REFERENCES chat '
          u'(ROWID) ON DELETE CASCADE, handle_id INTEGER REFERENCES handle '
          u'(ROWID) ON DELETE CASCADE, UNIQUE(chat_id, handle_id))'),
      u'chat_message_join': (
          u'CREATE TABLE chat_message_join (chat_id INTEGER REFERENCES chat '
          u'(ROWID) ON DELETE CASCADE, message_id INTEGER REFERENCES message '
          u'(ROWID) ON DELETE CASCADE, PRIMARY KEY (chat_id, message_id))'),
      u'deleted_messages': (
          u'CREATE TABLE deleted_messages (ROWID INTEGER PRIMARY KEY '
          u'AUTOINCREMENT UNIQUE, guid TEXT NOT NULL)'),
      u'handle': (
          u'CREATE TABLE handle (ROWID INTEGER PRIMARY KEY AUTOINCREMENT '
          u'UNIQUE, id TEXT NOT NULL, country TEXT, service TEXT NOT NULL, '
          u'uncanonicalized_id TEXT, UNIQUE (id, service) )'),
      u'message': (
          u'CREATE TABLE message (ROWID INTEGER PRIMARY KEY AUTOINCREMENT, '
          u'guid TEXT UNIQUE NOT NULL, text TEXT, replace INTEGER DEFAULT 0, '
          u'service_center TEXT, handle_id INTEGER DEFAULT 0, subject TEXT, '
          u'country TEXT, attributedBody BLOB, version INTEGER DEFAULT 0, type '
          u'INTEGER DEFAULT 0, service TEXT, account TEXT, account_guid TEXT, '
          u'error INTEGER DEFAULT 0, date INTEGER, date_read INTEGER, '
          u'date_delivered INTEGER, is_delivered INTEGER DEFAULT 0, '
          u'is_finished INTEGER DEFAULT 0, is_emote INTEGER DEFAULT 0, '
          u'is_from_me INTEGER DEFAULT 0, is_empty INTEGER DEFAULT 0, '
          u'is_delayed INTEGER DEFAULT 0, is_auto_reply INTEGER DEFAULT 0, '
          u'is_prepared INTEGER DEFAULT 0, is_read INTEGER DEFAULT 0, '
          u'is_system_message INTEGER DEFAULT 0, is_sent INTEGER DEFAULT 0, '
          u'has_dd_results INTEGER DEFAULT 0, is_service_message INTEGER '
          u'DEFAULT 0, is_forward INTEGER DEFAULT 0, was_downgraded INTEGER '
          u'DEFAULT 0, is_archive INTEGER DEFAULT 0, cache_has_attachments '
          u'INTEGER DEFAULT 0, cache_roomnames TEXT, was_data_detected INTEGER '
          u'DEFAULT 0, was_deduplicated INTEGER DEFAULT 0, is_audio_message '
          u'INTEGER DEFAULT 0, is_played INTEGER DEFAULT 0, date_played '
          u'INTEGER, item_type INTEGER DEFAULT 0, other_handle INTEGER DEFAULT '
          u'0, group_title TEXT, group_action_type INTEGER DEFAULT 0, '
          u'share_status INTEGER DEFAULT 0, share_direction INTEGER DEFAULT 0, '
          u'is_expirable INTEGER DEFAULT 0, expire_state INTEGER DEFAULT 0, '
          u'message_action_type INTEGER DEFAULT 0, message_source INTEGER '
          u'DEFAULT 0)'),
      u'message_attachment_join': (
          u'CREATE TABLE message_attachment_join (message_id INTEGER '
          u'REFERENCES message (ROWID) ON DELETE CASCADE, attachment_id '
          u'INTEGER REFERENCES attachment (ROWID) ON DELETE CASCADE, '
          u'UNIQUE(message_id, attachment_id))')}]

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

    event_data = IMessageEventData()
    event_data.attachment_location = row['attachment_location']
    event_data.imessage_id = row['imessage_id']
    event_data.message_type = row['message_type']
    event_data.offset = row['ROWID']
    event_data.query = query
    event_data.read_receipt = row['read_receipt']
    event_data.service = row['service']
    event_data.text = row['text']

    timestamp = row['date']
    date_time = dfdatetime_cocoa_time.CocoaTime(timestamp=timestamp)
    event = time_events.DateTimeValuesEvent(
        date_time, definitions.TIME_DESCRIPTION_CREATION)
    parser_mediator.ProduceEventWithEventData(event, event_data)


sqlite.SQLiteParser.RegisterPlugin(IMessagePlugin)
