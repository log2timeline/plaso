# -*- coding: utf-8 -*-
"""Plugin for the Zeitgeist SQLite database.

   Zeitgeist is a service which logs the user activities and events, anywhere
   from files opened to websites visited and conversations.
"""

from plaso.containers import time_events
from plaso.lib import eventdata
from plaso.parsers import sqlite
from plaso.parsers.sqlite_plugins import interface


class ZeitgeistEvent(time_events.JavaTimeEvent):
  """Convenience class for a Zeitgeist event."""

  DATA_TYPE = u'zeitgeist:activity'

  def __init__(self, java_time, row_id, subject_uri):
    """Initializes the event object.

    Args:
      java_time: The Java time value.
      row_id: The identifier of the corresponding row.
      subject_uri: The Zeitgeist event.
    """
    super(ZeitgeistEvent, self).__init__(
        java_time, eventdata.EventTimestamp.UNKNOWN)

    self.offset = row_id
    self.subject_uri = subject_uri


class ZeitgeistPlugin(interface.SQLitePlugin):
  """SQLite plugin for Zeitgeist activity database."""

  NAME = u'zeitgeist'
  DESCRIPTION = u'Parser for Zeitgeist activity SQLite database files.'

  # TODO: Explore the database more and make this parser cover new findings.

  QUERIES = [
      (u'SELECT id, timestamp, subj_uri FROM event_view',
       u'ParseZeitgeistEventRow')]

  REQUIRED_TABLES = frozenset([u'event', u'actor'])

  SCHEMAS = [
      {u'actor':
          u'CREATE TABLE actor ( id INTEGER PRIMARY KEY AUTOINCREMENT, value '
          u'VARCHAR UNIQUE )',
      u'event':
          u'CREATE TABLE event ( id INTEGER, timestamp INTEGER, '
          u'interpretation INTEGER, manifestation INTEGER, actor INTEGER, '
          u'payload INTEGER, subj_id INTEGER, subj_interpretation INTEGER, '
          u'subj_manifestation INTEGER, subj_origin INTEGER, subj_mimetype '
          u'INTEGER, subj_text INTEGER, subj_storage INTEGER, origin INTEGER, '
          u'subj_id_current INTEGER, CONSTRAINT interpretation_fk FOREIGN '
          u'KEY(interpretation) REFERENCES interpretation(id) ON DELETE '
          u'CASCADE, CONSTRAINT manifestation_fk FOREIGN KEY(manifestation) '
          u'REFERENCES manifestation(id) ON DELETE CASCADE, CONSTRAINT '
          u'actor_fk FOREIGN KEY(actor) REFERENCES actor(id) ON DELETE '
          u'CASCADE, CONSTRAINT origin_fk FOREIGN KEY(origin) REFERENCES '
          u'uri(id) ON DELETE CASCADE, CONSTRAINT payload_fk FOREIGN '
          u'KEY(payload) REFERENCES payload(id) ON DELETE CASCADE, CONSTRAINT '
          u'subj_id_fk FOREIGN KEY(subj_id) REFERENCES uri(id) ON DELETE '
          u'CASCADE, CONSTRAINT subj_id_current_fk FOREIGN '
          u'KEY(subj_id_current) REFERENCES uri(id) ON DELETE CASCADE, '
          u'CONSTRAINT subj_interpretation_fk FOREIGN '
          u'KEY(subj_interpretation) REFERENCES interpretation(id) ON DELETE '
          u'CASCADE, CONSTRAINT subj_manifestation_fk FOREIGN '
          u'KEY(subj_manifestation) REFERENCES manifestation(id) ON DELETE '
          u'CASCADE, CONSTRAINT subj_origin_fk FOREIGN KEY(subj_origin) '
          u'REFERENCES uri(id) ON DELETE CASCADE, CONSTRAINT subj_mimetype_fk '
          u'FOREIGN KEY(subj_mimetype) REFERENCES mimetype(id) ON DELETE '
          u'CASCADE, CONSTRAINT subj_text_fk FOREIGN KEY(subj_text) '
          u'REFERENCES text(id) ON DELETE CASCADE, CONSTRAINT subj_storage_fk '
          u'FOREIGN KEY(subj_storage) REFERENCES storage(id) ON DELETE '
          u'CASCADE, CONSTRAINT unique_event UNIQUE (timestamp, '
          u'interpretation, manifestation, actor, subj_id) )',
      u'extensions_conf':
          u'CREATE TABLE extensions_conf ( extension VARCHAR, key VARCHAR, '
          u'value BLOB, CONSTRAINT unique_extension UNIQUE (extension, key) )',
      u'interpretation':
          u'CREATE TABLE interpretation ( id INTEGER PRIMARY KEY '
          u'AUTOINCREMENT, value VARCHAR UNIQUE )',
      u'manifestation':
          u'CREATE TABLE manifestation ( id INTEGER PRIMARY KEY '
          u'AUTOINCREMENT, value VARCHAR UNIQUE )',
      u'mimetype':
          u'CREATE TABLE mimetype ( id INTEGER PRIMARY KEY AUTOINCREMENT, '
          u'value VARCHAR UNIQUE )',
      u'payload':
          u'CREATE TABLE payload (id INTEGER PRIMARY KEY, value BLOB)',
      u'schema_version':
          u'CREATE TABLE schema_version ( schema VARCHAR PRIMARY KEY ON '
          u'CONFLICT REPLACE, version INT )',
      u'storage':
          u'CREATE TABLE storage ( id INTEGER PRIMARY KEY, value VARCHAR '
          u'UNIQUE, state INTEGER, icon VARCHAR, display_name VARCHAR )',
      u'text':
          u'CREATE TABLE text ( id INTEGER PRIMARY KEY, value VARCHAR UNIQUE '
          u')',
      u'uri':
          u'CREATE TABLE uri ( id INTEGER PRIMARY KEY, value VARCHAR UNIQUE )'}]

  def ParseZeitgeistEventRow(
      self, parser_mediator, row, query=None, **unused_kwargs):
    """Parses zeitgeist event row.

    Args:
      parser_mediator (ParserMediator): parser mediator.
      row (sqlite3.Row): row resulting from the query.
      query (Optional[str]): query string.
    """
    # Note that pysqlite does not accept a Unicode string in row['string'] and
    # will raise "IndexError: Index must be int or string".

    event_object = ZeitgeistEvent(
        row['timestamp'], row['id'], row['subj_uri'])
    parser_mediator.ProduceEvent(event_object, query=query)


sqlite.SQLiteParser.RegisterPlugin(ZeitgeistPlugin)
