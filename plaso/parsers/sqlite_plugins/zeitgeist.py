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
          u'CREATE TABLE actor (\n                    id INTEGER PRIMARY KEY '
          u'AUTOINCREMENT,\n                    value VARCHAR UNIQUE\n '
          u')',
      u'event':
          u'CREATE TABLE event (\n                    id INTEGER,\n '
          u'timestamp INTEGER,\n                    interpretation INTEGER,\n '
          u'manifestation INTEGER,\n                    actor INTEGER,\n '
          u'payload INTEGER,\n                    subj_id INTEGER,\n '
          u'subj_interpretation INTEGER,\n '
          u'subj_manifestation INTEGER,\n                    subj_origin '
          u'INTEGER,\n                    subj_mimetype INTEGER,\n '
          u'subj_text INTEGER,\n                    subj_storage INTEGER,\n '
          u'origin INTEGER,\n                    subj_id_current INTEGER,\n '
          u'CONSTRAINT interpretation_fk\n                        FOREIGN '
          u'KEY(interpretation)\n                        REFERENCES '
          u'interpretation(id)\n                        ON DELETE CASCADE,\n '
          u'CONSTRAINT manifestation_fk\n                        FOREIGN '
          u'KEY(manifestation)\n                        REFERENCES '
          u'manifestation(id)\n                        ON DELETE CASCADE,\n '
          u'CONSTRAINT actor_fk\n                        FOREIGN KEY(actor)\n '
          u'REFERENCES actor(id)\n                        ON DELETE '
          u'CASCADE,\n                    CONSTRAINT origin_fk\n '
          u'FOREIGN KEY(origin)\n                        REFERENCES uri(id)\n '
          u'ON DELETE CASCADE,\n                    CONSTRAINT payload_fk\n '
          u'FOREIGN KEY(payload)\n                        REFERENCES '
          u'payload(id)\n                        ON DELETE CASCADE,\n '
          u'CONSTRAINT subj_id_fk\n                        FOREIGN '
          u'KEY(subj_id)\n                        REFERENCES uri(id)\n '
          u'ON DELETE CASCADE,\n                    CONSTRAINT '
          u'subj_id_current_fk\n                        FOREIGN '
          u'KEY(subj_id_current)\n                        REFERENCES '
          u'uri(id)\n                        ON DELETE CASCADE,\n '
          u'CONSTRAINT subj_interpretation_fk\n '
          u'FOREIGN KEY(subj_interpretation)\n '
          u'REFERENCES interpretation(id)\n                        ON DELETE '
          u'CASCADE,\n                    CONSTRAINT subj_manifestation_fk\n '
          u'FOREIGN KEY(subj_manifestation)\n '
          u'REFERENCES manifestation(id)\n                        ON DELETE '
          u'CASCADE,\n                    CONSTRAINT subj_origin_fk\n '
          u'FOREIGN KEY(subj_origin)\n                        REFERENCES '
          u'uri(id)\n                        ON DELETE CASCADE,\n '
          u'CONSTRAINT subj_mimetype_fk\n                        FOREIGN '
          u'KEY(subj_mimetype)\n                        REFERENCES '
          u'mimetype(id)\n                        ON DELETE CASCADE,\n '
          u'CONSTRAINT subj_text_fk\n                        FOREIGN '
          u'KEY(subj_text)\n                        REFERENCES text(id)\n '
          u'ON DELETE CASCADE,\n                    CONSTRAINT '
          u'subj_storage_fk\n                        FOREIGN '
          u'KEY(subj_storage)\n                        REFERENCES '
          u'storage(id)\n                        ON DELETE CASCADE,\n '
          u'CONSTRAINT unique_event UNIQUE (timestamp, interpretation,\n '
          u'manifestation, actor, subj_id)\n                )',
      u'extensions_conf':
          u'CREATE TABLE extensions_conf (\n                    extension '
          u'VARCHAR,\n                    key VARCHAR,\n '
          u'value BLOB,\n                    CONSTRAINT unique_extension '
          u'UNIQUE (extension, key)\n                )',
      u'interpretation':
          u'CREATE TABLE interpretation (\n                    id INTEGER '
          u'PRIMARY KEY AUTOINCREMENT,\n                    value VARCHAR '
          u'UNIQUE\n                )',
      u'manifestation':
          u'CREATE TABLE manifestation (\n                    id INTEGER '
          u'PRIMARY KEY AUTOINCREMENT,\n                    value VARCHAR '
          u'UNIQUE\n                )',
      u'mimetype':
          u'CREATE TABLE mimetype (\n                    id INTEGER PRIMARY '
          u'KEY AUTOINCREMENT,\n                    value VARCHAR UNIQUE\n '
          u')',
      u'payload':
          u'CREATE TABLE payload\n                    (id INTEGER PRIMARY '
          u'KEY, value BLOB)',
      u'schema_version':
          u'CREATE TABLE schema_version (\n                    schema VARCHAR '
          u'PRIMARY KEY ON CONFLICT REPLACE,\n                    version '
          u'INT\n                )',
      u'storage':
          u'CREATE TABLE storage (\n                    id INTEGER PRIMARY '
          u'KEY,\n                    value VARCHAR UNIQUE,\n '
          u'state INTEGER,\n                    icon VARCHAR,\n '
          u'display_name VARCHAR\n                )',
      u'text':
          u'CREATE TABLE text (\n                    id INTEGER PRIMARY '
          u'KEY,\n                    value VARCHAR UNIQUE\n                )',
      u'uri':
          u'CREATE TABLE uri (\n                    id INTEGER PRIMARY KEY,\n '
          u'value VARCHAR UNIQUE\n                )'}]

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
