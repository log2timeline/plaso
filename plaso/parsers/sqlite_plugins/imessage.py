# -*- coding: utf-8 -*-
"""This file contains a parser for the iMessage database on OSX and iOS.

iMessage and SMS data in OSX and iOS are stored in SQLite databases named
chat.db and sms.db respectively.
"""

from plaso.containers import time_events
from plaso.lib import eventdata
from plaso.parsers import sqlite
from plaso.parsers.sqlite_plugins import interface


class IMessageEvent(time_events.CocoaTimeEvent):
  """Convenience class for an iMessage and SMS event."""

  DATA_TYPE = u'imessage:event:chat'

  def __init__(
      self, cocoa_time, identifier, imessage_id, read_receipt,
      message_type, service, attachment_location, text):
    """Initializes the event object.

    Args:
      cocoa_time: an integer containing the Apple Cocoa time value - the number
                  of seconds passed since January 1, 2001 00:00:00 GMT.
      identifier: an integer containing the row number.
      imessage_id: a string containing the mobile number or email address the
                   message was sent to or received from.
      read_receipt: a boolean indicating that a message read receipt was
                    received.
      message_type: an integer indicating message was sent (1) or received (0).
      service: a string indicating SMS or iMessage.
      attachment: a boolean indicating that the message contained an attachment.
      text: content of the message.
    """
    super(IMessageEvent, self).__init__(
        cocoa_time, eventdata.EventTimestamp.CREATION_TIME)
    self.offset = identifier
    self.imessage_id = imessage_id
    self.read_receipt = read_receipt
    self.message_type = message_type
    self.service = service
    self.attachment_location = attachment_location
    self.text = text


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
  REQUIRED_TABLES = frozenset([u'message', u'handle', u'attachment',
                               u'message_attachment_join'])

  SCHEMAS = [
      {u'_SqliteDatabaseProperties':
          u'CREATE TABLE _SqliteDatabaseProperties (key TEXT, value TEXT, '
          u'UNIQUE(key))',
      u'attachment':
          u'CREATE TABLE attachment (ROWID INTEGER PRIMARY KEY AUTOINCREMENT, '
          u'guid TEXT UNIQUE NOT NULL, created_date INTEGER DEFAULT 0, '
          u'start_date INTEGER DEFAULT 0, filename TEXT, uti TEXT, mime_type '
          u'TEXT, transfer_state INTEGER DEFAULT 0, is_outgoing INTEGER '
          u'DEFAULT 0, user_info BLOB, transfer_name TEXT, total_bytes '
          u'INTEGER DEFAULT 0)',
      u'chat':
          u'CREATE TABLE chat (ROWID INTEGER PRIMARY KEY AUTOINCREMENT, guid '
          u'TEXT UNIQUE NOT NULL, style INTEGER, state INTEGER, account_id '
          u'TEXT, properties BLOB, chat_identifier TEXT, service_name TEXT, '
          u'room_name TEXT, account_login TEXT, is_archived INTEGER DEFAULT '
          u'0, last_addressed_handle TEXT, display_name TEXT, group_id TEXT, '
          u'is_filtered INTEGER, successful_query INTEGER)',
      u'chat_handle_join':
          u'CREATE TABLE chat_handle_join (chat_id INTEGER REFERENCES chat '
          u'(ROWID) ON DELETE CASCADE, handle_id INTEGER REFERENCES handle '
          u'(ROWID) ON DELETE CASCADE, UNIQUE(chat_id, handle_id))',
      u'chat_message_join':
          u'CREATE TABLE chat_message_join (chat_id INTEGER REFERENCES chat '
          u'(ROWID) ON DELETE CASCADE, message_id INTEGER REFERENCES message '
          u'(ROWID) ON DELETE CASCADE, PRIMARY KEY (chat_id, message_id))',
      u'deleted_messages':
          u'CREATE TABLE deleted_messages (ROWID INTEGER PRIMARY KEY '
          u'AUTOINCREMENT UNIQUE, guid TEXT NOT NULL)',
      u'handle':
          u'CREATE TABLE handle (ROWID INTEGER PRIMARY KEY AUTOINCREMENT '
          u'UNIQUE, id TEXT NOT NULL, country TEXT, service TEXT NOT NULL, '
          u'uncanonicalized_id TEXT, UNIQUE (id, service) )',
      u'message':
          u'CREATE TABLE message (ROWID INTEGER PRIMARY KEY AUTOINCREMENT, '
          u'guid TEXT UNIQUE NOT NULL, text TEXT, replace INTEGER DEFAULT 0, '
          u'service_center TEXT, handle_id INTEGER DEFAULT 0, subject TEXT, '
          u'country TEXT, attributedBody BLOB, version INTEGER DEFAULT 0, '
          u'type INTEGER DEFAULT 0, service TEXT, account TEXT, account_guid '
          u'TEXT, error INTEGER DEFAULT 0, date INTEGER, date_read INTEGER, '
          u'date_delivered INTEGER, is_delivered INTEGER DEFAULT 0, '
          u'is_finished INTEGER DEFAULT 0, is_emote INTEGER DEFAULT 0, '
          u'is_from_me INTEGER DEFAULT 0, is_empty INTEGER DEFAULT 0, '
          u'is_delayed INTEGER DEFAULT 0, is_auto_reply INTEGER DEFAULT 0, '
          u'is_prepared INTEGER DEFAULT 0, is_read INTEGER DEFAULT 0, '
          u'is_system_message INTEGER DEFAULT 0, is_sent INTEGER DEFAULT 0, '
          u'has_dd_results INTEGER DEFAULT 0, is_service_message INTEGER '
          u'DEFAULT 0, is_forward INTEGER DEFAULT 0, was_downgraded INTEGER '
          u'DEFAULT 0, is_archive INTEGER DEFAULT 0, cache_has_attachments '
          u'INTEGER DEFAULT 0, cache_roomnames TEXT, was_data_detected '
          u'INTEGER DEFAULT 0, was_deduplicated INTEGER DEFAULT 0, '
          u'is_audio_message INTEGER DEFAULT 0, is_played INTEGER DEFAULT 0, '
          u'date_played INTEGER, item_type INTEGER DEFAULT 0, other_handle '
          u'INTEGER DEFAULT 0, group_title TEXT, group_action_type INTEGER '
          u'DEFAULT 0, share_status INTEGER DEFAULT 0, share_direction '
          u'INTEGER DEFAULT 0, is_expirable INTEGER DEFAULT 0, expire_state '
          u'INTEGER DEFAULT 0, message_action_type INTEGER DEFAULT 0, '
          u'message_source INTEGER DEFAULT 0)',
      u'message_attachment_join':
          u'CREATE TABLE message_attachment_join (message_id INTEGER '
          u'REFERENCES message (ROWID) ON DELETE CASCADE, attachment_id '
          u'INTEGER REFERENCES attachment (ROWID) ON DELETE CASCADE, '
          u'UNIQUE(message_id, attachment_id))'}]

  def ParseMessageRow(self, parser_mediator, row, query=None, **unused_kwargs):
    """Parses a message row.

    Args:
      parser_mediator (ParserMediator): parser mediator.
      row (sqlite3.Row): row resulting from the query.
      query (Optional[str]): query string.
    """
    # Note that pysqlite does not accept a Unicode string in row['string'] and
    # will raise "IndexError: Index must be int or string".
    event_object = IMessageEvent(
        row['date'], row['ROWID'], row['imessage_id'], row['read_receipt'],
        row['message_type'], row['service'], row['attachment_location'],
        row['text'])
    parser_mediator.ProduceEvent(event_object, query=query)

sqlite.SQLiteParser.RegisterPlugin(IMessagePlugin)
