# -*- coding: utf-8 -*-
"""This file contains a parser for the Android contacts2 Call History.

Android Call History is stored in SQLite database files named contacts2.db.
"""

from plaso.containers import time_events
from plaso.lib import py2to3
from plaso.parsers import sqlite
from plaso.parsers.sqlite_plugins import interface


class AndroidCallEvent(time_events.JavaTimeEvent):
  """Convenience class for an Android Call History event."""

  DATA_TYPE = u'android:event:call'

  def __init__(
      self, java_time, usage, identifier, number, name, duration, call_type):
    """Initializes the event object.

    Args:
      java_time: The Java time value.
      usage: The description of the usage of the time value.
      identifier: The row identifier.
      number: The phone number associated to the remote party.
      duration: The number of seconds the call lasted.
      call_type: Incoming, Outgoing, or Missed.
    """
    super(AndroidCallEvent, self).__init__(java_time, usage)
    self.offset = identifier
    self.number = number
    self.name = name
    self.duration = duration
    self.call_type = call_type


class AndroidCallPlugin(interface.SQLitePlugin):
  """Parse Android contacts2 database."""

  NAME = u'android_calls'
  DESCRIPTION = u'Parser for Android calls SQLite database files.'

  REQUIRED_TABLES = frozenset([u'calls'])

  # Define the needed queries.
  QUERIES = [
      (u'SELECT _id AS id, date, number, name, duration, type FROM calls',
       u'ParseCallsRow')]

  SCHEMAS = [
      {u'addr':
          u'CREATE TABLE addr (_id INTEGER PRIMARY KEY,msg_id '
          u'INTEGER,contact_id INTEGER,address TEXT,type INTEGER,charset '
          u'INTEGER)',
      u'android_metadata':
          u'CREATE TABLE android_metadata (locale TEXT)',
      u'attachments':
          u'CREATE TABLE attachments (sms_id INTEGER,content_url TEXT,offset '
          u'INTEGER)',
      u'canonical_addresses':
          u'CREATE TABLE canonical_addresses (_id INTEGER PRIMARY KEY '
          u'AUTOINCREMENT,address TEXT)',
      u'drm':
          u'CREATE TABLE drm (_id INTEGER PRIMARY KEY,_data TEXT)',
      u'part':
          u'CREATE TABLE part (_id INTEGER PRIMARY KEY AUTOINCREMENT,mid '
          u'INTEGER,seq INTEGER DEFAULT 0,ct TEXT,name TEXT,chset INTEGER,cd '
          u'TEXT,fn TEXT,cid TEXT,cl TEXT,ctt_s INTEGER,ctt_t TEXT,_data '
          u'TEXT,text TEXT)',
      u'pdu':
          u'CREATE TABLE pdu (_id INTEGER PRIMARY KEY AUTOINCREMENT,thread_id '
          u'INTEGER,date INTEGER,date_sent INTEGER DEFAULT 0,msg_box '
          u'INTEGER,read INTEGER DEFAULT 0,m_id TEXT,sub TEXT,sub_cs '
          u'INTEGER,ct_t TEXT,ct_l TEXT,exp INTEGER,m_cls TEXT,m_type '
          u'INTEGER,v INTEGER,m_size INTEGER,pri INTEGER,rr INTEGER,rpt_a '
          u'INTEGER,resp_st INTEGER,st INTEGER,tr_id TEXT,retr_st '
          u'INTEGER,retr_txt TEXT,retr_txt_cs INTEGER,read_status '
          u'INTEGER,ct_cls INTEGER,resp_txt TEXT,d_tm INTEGER,d_rpt '
          u'INTEGER,locked INTEGER DEFAULT 0,seen INTEGER DEFAULT 0,text_only '
          u'INTEGER DEFAULT 0)',
      u'pending_msgs':
          u'CREATE TABLE pending_msgs (_id INTEGER PRIMARY KEY,proto_type '
          u'INTEGER,msg_id INTEGER,msg_type INTEGER,err_type INTEGER,err_code '
          u'INTEGER,retry_index INTEGER NOT NULL DEFAULT 0,due_time '
          u'INTEGER,last_try INTEGER)',
      u'rate':
          u'CREATE TABLE rate (sent_time INTEGER)',
      u'raw':
          u'CREATE TABLE raw (_id INTEGER PRIMARY KEY,date '
          u'INTEGER,reference_number INTEGER,count INTEGER,sequence '
          u'INTEGER,destination_port INTEGER,address TEXT,pdu TEXT)',
      u'sms':
          u'CREATE TABLE sms (_id INTEGER PRIMARY KEY,thread_id '
          u'INTEGER,address TEXT,person INTEGER,date INTEGER,date_sent '
          u'INTEGER DEFAULT 0,protocol INTEGER,read INTEGER DEFAULT 0,status '
          u'INTEGER DEFAULT -1,type INTEGER,reply_path_present '
          u'INTEGER,subject TEXT,body TEXT,service_center TEXT,locked INTEGER '
          u'DEFAULT 0,error_code INTEGER DEFAULT 0,seen INTEGER DEFAULT 0)',
      u'sr_pending':
          u'CREATE TABLE sr_pending (reference_number INTEGER,action '
          u'TEXT,data TEXT)',
      u'threads':
          u'CREATE TABLE threads (_id INTEGER PRIMARY KEY AUTOINCREMENT,date '
          u'INTEGER DEFAULT 0,message_count INTEGER DEFAULT 0,recipient_ids '
          u'TEXT,snippet TEXT,snippet_cs INTEGER DEFAULT 0,read INTEGER '
          u'DEFAULT 1,type INTEGER DEFAULT 0,error INTEGER DEFAULT '
          u'0,has_attachment INTEGER DEFAULT 0)',
      u'words':
          u'CREATE VIRTUAL TABLE words USING FTS3 (_id INTEGER PRIMARY KEY, '
          u'index_text TEXT, source_id INTEGER, table_to_use INTEGER)',
      u'words_content':
          u'CREATE TABLE \'words_content\'(docid INTEGER PRIMARY KEY, '
          u'\'c0_id\', \'c1index_text\', \'c2source_id\', \'c3table_to_use\')',
      u'words_segdir':
          u'CREATE TABLE \'words_segdir\'(level INTEGER,idx '
          u'INTEGER,start_block INTEGER,leaves_end_block INTEGER,end_block '
          u'INTEGER,root BLOB,PRIMARY KEY(level, idx))',
      u'words_segments':
          u'CREATE TABLE \'words_segments\'(blockid INTEGER PRIMARY KEY, '
          u'block BLOB)'}]

  CALL_TYPE = {
      1: u'INCOMING',
      2: u'OUTGOING',
      3: u'MISSED'}

  def ParseCallsRow(self, parser_mediator, row, query=None, **unused_kwargs):
    """Parses a Call record row.

    Args:
      parser_mediator (ParserMediator): parser mediator.
      row (sqlite3.Row): row resulting from the query.
      query (Optional[str]): query string.
    """
    # Note that pysqlite does not accept a Unicode string in row['string'] and
    # will raise "IndexError: Index must be int or string".

    call_type = self.CALL_TYPE.get(row['type'], u'UNKNOWN')

    event_object = AndroidCallEvent(
        row['date'], u'Call Started', row['id'], row['number'], row['name'],
        row['duration'], call_type)
    parser_mediator.ProduceEvent(event_object, query=query)

    duration = row['duration']
    if isinstance(duration, py2to3.STRING_TYPES):
      try:
        duration = int(duration, 10)
      except ValueError:
        duration = 0

    if duration:
      # The duration is in seconds and the date value in milliseconds.
      duration *= 1000
      event_object = AndroidCallEvent(
          row['date'] + duration, u'Call Ended', row['id'], row['number'],
          row['name'], row['duration'], call_type)
      parser_mediator.ProduceEvent(event_object, query=query)



sqlite.SQLiteParser.RegisterPlugin(AndroidCallPlugin)
