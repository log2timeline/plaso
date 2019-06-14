# -*- coding: utf-8 -*-
"""This file contains a parser for the Android SMS database.

Android SMS messages are stored in SQLite database files named mmssms.dbs.
"""

from __future__ import unicode_literals

from dfdatetime import java_time as dfdatetime_java_time

from plaso.containers import events
from plaso.containers import time_events
from plaso.lib import definitions
from plaso.parsers import sqlite
from plaso.parsers.sqlite_plugins import interface


class AndroidSMSEventData(events.EventData):
  """Android SMS event data.

  Attributes:
    address (str): phone number associated to the sender or receiver.
    body (str): content of the SMS text message.
    sms_read (str): message read status, either Read or Unread.
    sms_type (str): message type, either Sent or Received.
  """

  DATA_TYPE = 'android:messaging:sms'

  def __init__(self):
    """Initializes event data."""
    super(AndroidSMSEventData, self).__init__(data_type=self.DATA_TYPE)
    self.address = None
    self.body = None
    self.sms_read = None
    self.sms_type = None


class AndroidSMSPlugin(interface.SQLitePlugin):
  """Parser for Android SMS databases."""

  NAME = 'android_sms'
  DESCRIPTION = 'Parser for Android text messages SQLite database files.'

  REQUIRED_STRUCTURE = {
      'sms': frozenset([
          '_id', 'address', 'date', 'read', 'type', 'body'])}

  QUERIES = [
      ('SELECT _id AS id, address, date, read, type, body FROM sms',
       'ParseSmsRow')]

  SCHEMAS = [{
      'addr': (
          'CREATE TABLE addr (_id INTEGER PRIMARY KEY, msg_id INTEGER, '
          'contact_id INTEGER, address TEXT, type INTEGER, charset INTEGER)'),
      'android_metadata': (
          'CREATE TABLE android_metadata (locale TEXT)'),
      'attachments': (
          'CREATE TABLE attachments (sms_id INTEGER, content_url TEXT, offset '
          'INTEGER)'),
      'canonical_addresses': (
          'CREATE TABLE canonical_addresses (_id INTEGER PRIMARY KEY '
          'AUTOINCREMENT, address TEXT)'),
      'drm': (
          'CREATE TABLE drm (_id INTEGER PRIMARY KEY, _data TEXT)'),
      'part': (
          'CREATE TABLE part (_id INTEGER PRIMARY KEY AUTOINCREMENT, mid '
          'INTEGER, seq INTEGER DEFAULT 0, ct TEXT, name TEXT, chset INTEGER, '
          'cd TEXT, fn TEXT, cid TEXT, cl TEXT, ctt_s INTEGER, ctt_t TEXT, '
          '_data TEXT, text TEXT)'),
      'pd': (
          'CREATE TABLE pdu (_id INTEGER PRIMARY KEY AUTOINCREMENT, thread_id '
          'INTEGER, date INTEGER, date_sent INTEGER DEFAULT 0, msg_box '
          'INTEGER, read INTEGER DEFAULT 0, m_id TEXT, sub TEXT, sub_cs '
          'INTEGER, ct_t TEXT, ct_l TEXT, exp INTEGER, m_cls TEXT, m_type '
          'INTEGER, v INTEGER, m_size INTEGER, pri INTEGER, rr INTEGER, rpt_a '
          'INTEGER, resp_st INTEGER, st INTEGER, tr_id TEXT, retr_st INTEGER, '
          'retr_txt TEXT, retr_txt_cs INTEGER, read_status INTEGER, ct_cls '
          'INTEGER, resp_txt TEXT, d_tm INTEGER, d_rpt INTEGER, locked '
          'INTEGER DEFAULT 0, seen INTEGER DEFAULT 0, text_only INTEGER '
          'DEFAULT 0)'),
      'pending_msgs': (
          'CREATE TABLE pending_msgs (_id INTEGER PRIMARY KEY, proto_type '
          'INTEGER, msg_id INTEGER, msg_type INTEGER, err_type INTEGER, '
          'err_code INTEGER, retry_index INTEGER NOT NULL DEFAULT 0, due_time '
          'INTEGER, last_try INTEGER)'),
      'rate': (
          'CREATE TABLE rate (sent_time INTEGER)'),
      'raw': (
          'CREATE TABLE raw (_id INTEGER PRIMARY KEY, date INTEGER, '
          'reference_number INTEGER, count INTEGER, sequence INTEGER, '
          'destination_port INTEGER, address TEXT, pdu TEXT)'),
      'sms': (
          'CREATE TABLE sms (_id INTEGER PRIMARY KEY, thread_id INTEGER, '
          'address TEXT, person INTEGER, date INTEGER, date_sent INTEGER '
          'DEFAULT 0, protocol INTEGER, read INTEGER DEFAULT 0, status '
          'INTEGER DEFAULT -1, type INTEGER, reply_path_present INTEGER, '
          'subject TEXT, body TEXT, service_center TEXT, locked INTEGER '
          'DEFAULT 0, error_code INTEGER DEFAULT 0, seen INTEGER DEFAULT 0)'),
      'sr_pending': (
          'CREATE TABLE sr_pending (reference_number INTEGER, action TEXT, '
          'data TEXT)'),
      'threads': (
          'CREATE TABLE threads (_id INTEGER PRIMARY KEY AUTOINCREMENT, date '
          'INTEGER DEFAULT 0, message_count INTEGER DEFAULT 0, recipient_ids '
          'TEXT, snippet TEXT, snippet_cs INTEGER DEFAULT 0, read INTEGER '
          'DEFAULT 1, type INTEGER DEFAULT 0, error INTEGER DEFAULT 0, '
          'has_attachment INTEGER DEFAULT 0)'),
      'words': (
          'CREATE VIRTUAL TABLE words USING FTS3 (_id INTEGER PRIMARY KEY, '
          'index_text TEXT, source_id INTEGER, table_to_use INTEGER)'),
      'words_content': (
          'CREATE TABLE \'words_content\'(docid INTEGER PRIMARY KEY, '
          '\'c0_id\', \'c1index_text\', \'c2source_id\', \'c3table_to_use\')'),
      'words_segdir': (
          'CREATE TABLE \'words_segdir\'(level INTEGER, idx INTEGER, '
          'start_block INTEGER, leaves_end_block INTEGER, end_block INTEGER, '
          'root BLOB, PRIMARY KEY(level, idx))'),
      'words_segments': (
          'CREATE TABLE \'words_segments\'(blockid INTEGER PRIMARY KEY, block '
          'BLOB)')}]

  # TODO: Move this functionality to the formatter.
  SMS_TYPE = {
      1: 'RECEIVED',
      2: 'SENT'}
  SMS_READ = {
      0: 'UNREAD',
      1: 'READ'}

  def ParseSmsRow(self, parser_mediator, query, row, **unused_kwargs):
    """Parses an SMS row.

    Args:
      parser_mediator (ParserMediator): mediates interactions between parsers
          and other components, such as storage and dfvfs.
      query (str): query that created the row.
      row (sqlite3.Row): row.
    """
    query_hash = hash(query)

    sms_read = self._GetRowValue(query_hash, row, 'read')
    sms_type = self._GetRowValue(query_hash, row, 'type')

    event_data = AndroidSMSEventData()
    event_data.address = self._GetRowValue(query_hash, row, 'address')
    event_data.body = self._GetRowValue(query_hash, row, 'body')
    event_data.offset = self._GetRowValue(query_hash, row, 'id')
    event_data.query = query
    event_data.sms_read = self.SMS_READ.get(sms_read, 'UNKNOWN')
    event_data.sms_type = self.SMS_TYPE.get(sms_type, 'UNKNOWN')

    timestamp = self._GetRowValue(query_hash, row, 'date')
    date_time = dfdatetime_java_time.JavaTime(timestamp=timestamp)
    event = time_events.DateTimeValuesEvent(
        date_time, definitions.TIME_DESCRIPTION_CREATION)
    parser_mediator.ProduceEventWithEventData(event, event_data)


sqlite.SQLiteParser.RegisterPlugin(AndroidSMSPlugin)
