# -*- coding: utf-8 -*-
"""This file contains a parser for the Android SMS database.

Android SMS messages are stored in SQLite database files named mmssms.dbs.
"""

from plaso.containers import time_events
from plaso.lib import eventdata
from plaso.parsers import sqlite
from plaso.parsers.sqlite_plugins import interface


class AndroidSMSEvent(time_events.JavaTimeEvent):
  """Convenience class for an Android SMS event."""

  DATA_TYPE = u'android:messaging:sms'

  def __init__(self, java_time, identifier, address, sms_read, sms_type, body):
    """Initializes the event object.

    Args:
      java_time: The Java time value.
      identifier: a numeric type containing the identifier of the row containing
                the event information.
      address: a string containing the phone number associated to the
              sender/receiver.
      sms_read: a string containing the message read status, either
                Read or Unread.
      sms_type: a string containing the message type, either Sent or Received.
      body: a string containing the content of the SMS text message.
    """
    super(AndroidSMSEvent, self).__init__(
        java_time, eventdata.EventTimestamp.CREATION_TIME)
    self.offset = identifier
    self.address = address
    self.sms_read = sms_read
    self.sms_type = sms_type
    self.body = body


class AndroidSMSPlugin(interface.SQLitePlugin):
  """Parse Android SMS database."""

  NAME = u'android_sms'
  DESCRIPTION = u'Parser for Android text messages SQLite database files.'

  # Define the needed queries.
  QUERIES = [
      (u'SELECT _id AS id, address, date, read, type, body FROM sms',
       u'ParseSmsRow')]

  # The required tables.
  REQUIRED_TABLES = frozenset([u'sms'])

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
       u'INTEGER,ct_t TEXT,ct_l TEXT,exp INTEGER,m_cls TEXT,m_type INTEGER,v '
       u'INTEGER,m_size INTEGER,pri INTEGER,rr INTEGER,rpt_a INTEGER,resp_st '
       u'INTEGER,st INTEGER,tr_id TEXT,retr_st INTEGER,retr_txt '
       u'TEXT,retr_txt_cs INTEGER,read_status INTEGER,ct_cls '
       u'INTEGER,resp_txt TEXT,d_tm INTEGER,d_rpt INTEGER,locked INTEGER '
       u'DEFAULT 0,seen INTEGER DEFAULT 0,text_only INTEGER DEFAULT 0)',
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
       u'CREATE TABLE sms (_id INTEGER PRIMARY KEY,thread_id INTEGER,address '
       u'TEXT,person INTEGER,date INTEGER,date_sent INTEGER DEFAULT '
       u'0,protocol INTEGER,read INTEGER DEFAULT 0,status INTEGER DEFAULT '
       u'-1,type INTEGER,reply_path_present INTEGER,subject TEXT,body '
       u'TEXT,service_center TEXT,locked INTEGER DEFAULT 0,error_code '
       u'INTEGER DEFAULT 0,seen INTEGER DEFAULT 0)',
       u'sr_pending':
       u'CREATE TABLE sr_pending (reference_number INTEGER,action TEXT,data '
       u'TEXT)',
       u'threads':
       u'CREATE TABLE threads (_id INTEGER PRIMARY KEY AUTOINCREMENT,date '
       u'INTEGER DEFAULT 0,message_count INTEGER DEFAULT 0,recipient_ids '
       u'TEXT,snippet TEXT,snippet_cs INTEGER DEFAULT 0,read INTEGER DEFAULT '
       u'1,type INTEGER DEFAULT 0,error INTEGER DEFAULT 0,has_attachment '
       u'INTEGER DEFAULT 0)',
       u'words':
       u'CREATE VIRTUAL TABLE words USING FTS3 (_id INTEGER PRIMARY KEY, '
       u'index_text TEXT, source_id INTEGER, table_to_use INTEGER)',
       u'words_content':
       u'CREATE TABLE \'words_content\'(docid INTEGER PRIMARY KEY, '
       u'\'c0_id\', \'c1index_text\', \'c2source_id\', \'c3table_to_use\')',
       u'words_segdir':
       u'CREATE TABLE \'words_segdir\'(level INTEGER,idx INTEGER,start_block '
       u'INTEGER,leaves_end_block INTEGER,end_block INTEGER,root '
       u'BLOB,PRIMARY KEY(level, idx))',
       u'words_segments':
       u'CREATE TABLE \'words_segments\'(blockid INTEGER PRIMARY KEY, block '
       u'BLOB)'}]

  # TODO: Move this functionality to the formatter.
  SMS_TYPE = {
      1: u'RECEIVED',
      2: u'SENT'}
  SMS_READ = {
      0: u'UNREAD',
      1: u'READ'}

  def ParseSmsRow(self, parser_mediator, row, query=None, **unused_kwargs):
    """Parses an SMS row.

    Args:
      parser_mediator (ParserMediator): parser mediator.
      row (sqlite3.Row): row resulting from the query.
      query (Optional[str]): query string.
    """
    # Note that pysqlite does not accept a Unicode string in row['string'] and
    # will raise "IndexError: Index must be int or string".

    sms_type = self.SMS_TYPE.get(row['type'], u'UNKNOWN')
    sms_read = self.SMS_READ.get(row['read'], u'UNKNOWN')

    event_object = AndroidSMSEvent(
        row['date'], row['id'], row['address'], sms_read, sms_type,
        row['body'])
    parser_mediator.ProduceEvent(event_object, query=query)


sqlite.SQLiteParser.RegisterPlugin(AndroidSMSPlugin)
