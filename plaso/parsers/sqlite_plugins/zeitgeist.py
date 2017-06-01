# -*- coding: utf-8 -*-
"""Plugin for the Zeitgeist SQLite database.

Zeitgeist is a service which logs the user activities and events, anywhere
from files opened to websites visited and conversations.
"""

from dfdatetime import java_time as dfdatetime_java_time

from plaso.containers import events
from plaso.containers import time_events
from plaso.lib import definitions
from plaso.parsers import sqlite
from plaso.parsers.sqlite_plugins import interface


class ZeitgeistActivityEventData(events.EventData):
  """Zeitgeist activity event data.

  Attributes:
    subject_uri (str): subject URI.
  """

  DATA_TYPE = u'zeitgeist:activity'

  def __init__(self):
    """Initializes event data."""
    super(ZeitgeistActivityEventData, self).__init__(data_type=self.DATA_TYPE)
    self.subject_uri = None


class ZeitgeistActivityDatabasePlugin(interface.SQLitePlugin):
  """SQLite plugin for Zeitgeist activity database."""

  NAME = u'zeitgeist'
  DESCRIPTION = u'Parser for Zeitgeist activity SQLite database files.'

  # TODO: Explore the database more and make this parser cover new findings.

  QUERIES = [
      (u'SELECT id, timestamp, subj_uri FROM event_view',
       u'ParseZeitgeistEventRow')]

  REQUIRED_TABLES = frozenset([u'event', u'actor'])

  SCHEMAS = [{
      u'actor': (
          u'CREATE TABLE actor ( id INTEGER PRIMARY KEY AUTOINCREMENT, value '
          u'VARCHAR UNIQUE )'),
      u'event': (
          u'CREATE TABLE event ( id INTEGER, timestamp INTEGER, interpretation '
          u'INTEGER, manifestation INTEGER, actor INTEGER, payload INTEGER, '
          u'subj_id INTEGER, subj_interpretation INTEGER, subj_manifestation '
          u'INTEGER, subj_origin INTEGER, subj_mimetype INTEGER, subj_text '
          u'INTEGER, subj_storage INTEGER, origin INTEGER, subj_id_current '
          u'INTEGER, CONSTRAINT interpretation_fk FOREIGN KEY(interpretation) '
          u'REFERENCES interpretation(id) ON DELETE CASCADE, CONSTRAINT '
          u'manifestation_fk FOREIGN KEY(manifestation) REFERENCES '
          u'manifestation(id) ON DELETE CASCADE, CONSTRAINT actor_fk FOREIGN '
          u'KEY(actor) REFERENCES actor(id) ON DELETE CASCADE, CONSTRAINT '
          u'origin_fk FOREIGN KEY(origin) REFERENCES uri(id) ON DELETE '
          u'CASCADE, CONSTRAINT payload_fk FOREIGN KEY(payload) REFERENCES '
          u'payload(id) ON DELETE CASCADE, CONSTRAINT subj_id_fk FOREIGN '
          u'KEY(subj_id) REFERENCES uri(id) ON DELETE CASCADE, CONSTRAINT '
          u'subj_id_current_fk FOREIGN KEY(subj_id_current) REFERENCES uri(id) '
          u'ON DELETE CASCADE, CONSTRAINT subj_interpretation_fk FOREIGN '
          u'KEY(subj_interpretation) REFERENCES interpretation(id) ON DELETE '
          u'CASCADE, CONSTRAINT subj_manifestation_fk FOREIGN '
          u'KEY(subj_manifestation) REFERENCES manifestation(id) ON DELETE '
          u'CASCADE, CONSTRAINT subj_origin_fk FOREIGN KEY(subj_origin) '
          u'REFERENCES uri(id) ON DELETE CASCADE, CONSTRAINT subj_mimetype_fk '
          u'FOREIGN KEY(subj_mimetype) REFERENCES mimetype(id) ON DELETE '
          u'CASCADE, CONSTRAINT subj_text_fk FOREIGN KEY(subj_text) REFERENCES '
          u'text(id) ON DELETE CASCADE, CONSTRAINT subj_storage_fk FOREIGN '
          u'KEY(subj_storage) REFERENCES storage(id) ON DELETE CASCADE, '
          u'CONSTRAINT unique_event UNIQUE (timestamp, interpretation, '
          u'manifestation, actor, subj_id) )'),
      u'extensions_conf': (
          u'CREATE TABLE extensions_conf ( extension VARCHAR, key VARCHAR, '
          u'value BLOB, CONSTRAINT unique_extension UNIQUE (extension, key) )'),
      u'interpretation': (
          u'CREATE TABLE interpretation ( id INTEGER PRIMARY KEY '
          u'AUTOINCREMENT, value VARCHAR UNIQUE )'),
      u'manifestation': (
          u'CREATE TABLE manifestation ( id INTEGER PRIMARY KEY AUTOINCREMENT, '
          u'value VARCHAR UNIQUE )'),
      u'mimetype': (
          u'CREATE TABLE mimetype ( id INTEGER PRIMARY KEY AUTOINCREMENT, '
          u'value VARCHAR UNIQUE )'),
      u'payload': (
          u'CREATE TABLE payload (id INTEGER PRIMARY KEY, value BLOB)'),
      u'schema_version': (
          u'CREATE TABLE schema_version ( schema VARCHAR PRIMARY KEY ON '
          u'CONFLICT REPLACE, version INT )'),
      u'storage': (
          u'CREATE TABLE storage ( id INTEGER PRIMARY KEY, value VARCHAR '
          u'UNIQUE, state INTEGER, icon VARCHAR, display_name VARCHAR )'),
      u'text': (
          u'CREATE TABLE text ( id INTEGER PRIMARY KEY, value VARCHAR '
          u'UNIQUE )'),
      u'uri': (
          u'CREATE TABLE uri ( id INTEGER PRIMARY KEY, value VARCHAR '
          u'UNIQUE )')}]

  def ParseZeitgeistEventRow(
      self, parser_mediator, row, query=None, **unused_kwargs):
    """Parses zeitgeist event row.

    Args:
      parser_mediator (ParserMediator): mediates interactions between parsers
          and other components, such as storage and dfvfs.
      row (sqlite3.Row): row.
      query (Optional[str]): query.
    """
    # Note that pysqlite does not accept a Unicode string in row['string'] and
    # will raise "IndexError: Index must be int or string".

    event_data = ZeitgeistActivityEventData()
    event_data.offset = row['id']
    event_data.query = query
    event_data.subject_uri = row['subj_uri']

    date_time = dfdatetime_java_time.JavaTime(timestamp=row['timestamp'])
    event = time_events.DateTimeValuesEvent(
        date_time, definitions.TIME_DESCRIPTION_UNKNOWN)
    parser_mediator.ProduceEventWithEventData(event, event_data)


sqlite.SQLiteParser.RegisterPlugin(ZeitgeistActivityDatabasePlugin)
