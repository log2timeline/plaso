# -*- coding: utf-8 -*-
"""Plugin for the Zeitgeist SQLite database.

Zeitgeist is a service which logs the user activities and events, anywhere
from files opened to websites visited and conversations.
"""

from __future__ import unicode_literals

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

  DATA_TYPE = 'zeitgeist:activity'

  def __init__(self):
    """Initializes event data."""
    super(ZeitgeistActivityEventData, self).__init__(data_type=self.DATA_TYPE)
    self.subject_uri = None


class ZeitgeistActivityDatabasePlugin(interface.SQLitePlugin):
  """SQLite plugin for Zeitgeist activity database."""

  NAME = 'zeitgeist'
  DESCRIPTION = 'Parser for Zeitgeist activity SQLite database files.'

  # TODO: Explore the database more and make this parser cover new findings.

  REQUIRED_STRUCTURE = {
      'event_view': frozenset([
          'id', 'timestamp', 'subj_uri']),
      'event': frozenset([
          'id', 'timestamp']),
      'actor': frozenset([])}

  QUERIES = [
      ('SELECT id, timestamp, subj_uri FROM event_view',
       'ParseZeitgeistEventRow')]

  SCHEMAS = [{
      'actor': (
          'CREATE TABLE actor ( id INTEGER PRIMARY KEY AUTOINCREMENT, value '
          'VARCHAR UNIQUE )'),
      'event': (
          'CREATE TABLE event ( id INTEGER, timestamp INTEGER, interpretation '
          'INTEGER, manifestation INTEGER, actor INTEGER, payload INTEGER, '
          'subj_id INTEGER, subj_interpretation INTEGER, subj_manifestation '
          'INTEGER, subj_origin INTEGER, subj_mimetype INTEGER, subj_text '
          'INTEGER, subj_storage INTEGER, origin INTEGER, subj_id_current '
          'INTEGER, CONSTRAINT interpretation_fk FOREIGN KEY(interpretation) '
          'REFERENCES interpretation(id) ON DELETE CASCADE, CONSTRAINT '
          'manifestation_fk FOREIGN KEY(manifestation) REFERENCES '
          'manifestation(id) ON DELETE CASCADE, CONSTRAINT actor_fk FOREIGN '
          'KEY(actor) REFERENCES actor(id) ON DELETE CASCADE, CONSTRAINT '
          'origin_fk FOREIGN KEY(origin) REFERENCES uri(id) ON DELETE '
          'CASCADE, CONSTRAINT payload_fk FOREIGN KEY(payload) REFERENCES '
          'payload(id) ON DELETE CASCADE, CONSTRAINT subj_id_fk FOREIGN '
          'KEY(subj_id) REFERENCES uri(id) ON DELETE CASCADE, CONSTRAINT '
          'subj_id_current_fk FOREIGN KEY(subj_id_current) REFERENCES uri(id) '
          'ON DELETE CASCADE, CONSTRAINT subj_interpretation_fk FOREIGN '
          'KEY(subj_interpretation) REFERENCES interpretation(id) ON DELETE '
          'CASCADE, CONSTRAINT subj_manifestation_fk FOREIGN '
          'KEY(subj_manifestation) REFERENCES manifestation(id) ON DELETE '
          'CASCADE, CONSTRAINT subj_origin_fk FOREIGN KEY(subj_origin) '
          'REFERENCES uri(id) ON DELETE CASCADE, CONSTRAINT subj_mimetype_fk '
          'FOREIGN KEY(subj_mimetype) REFERENCES mimetype(id) ON DELETE '
          'CASCADE, CONSTRAINT subj_text_fk FOREIGN KEY(subj_text) REFERENCES '
          'text(id) ON DELETE CASCADE, CONSTRAINT subj_storage_fk FOREIGN '
          'KEY(subj_storage) REFERENCES storage(id) ON DELETE CASCADE, '
          'CONSTRAINT unique_event UNIQUE (timestamp, interpretation, '
          'manifestation, actor, subj_id) )'),
      'extensions_conf': (
          'CREATE TABLE extensions_conf ( extension VARCHAR, key VARCHAR, '
          'value BLOB, CONSTRAINT unique_extension UNIQUE (extension, key) )'),
      'interpretation': (
          'CREATE TABLE interpretation ( id INTEGER PRIMARY KEY '
          'AUTOINCREMENT, value VARCHAR UNIQUE )'),
      'manifestation': (
          'CREATE TABLE manifestation ( id INTEGER PRIMARY KEY AUTOINCREMENT, '
          'value VARCHAR UNIQUE )'),
      'mimetype': (
          'CREATE TABLE mimetype ( id INTEGER PRIMARY KEY AUTOINCREMENT, '
          'value VARCHAR UNIQUE )'),
      'payload': (
          'CREATE TABLE payload (id INTEGER PRIMARY KEY, value BLOB)'),
      'schema_version': (
          'CREATE TABLE schema_version ( schema VARCHAR PRIMARY KEY ON '
          'CONFLICT REPLACE, version INT )'),
      'storage': (
          'CREATE TABLE storage ( id INTEGER PRIMARY KEY, value VARCHAR '
          'UNIQUE, state INTEGER, icon VARCHAR, display_name VARCHAR )'),
      'text': (
          'CREATE TABLE text ( id INTEGER PRIMARY KEY, value VARCHAR '
          'UNIQUE )'),
      'uri': (
          'CREATE TABLE uri ( id INTEGER PRIMARY KEY, value VARCHAR '
          'UNIQUE )')}]

  def ParseZeitgeistEventRow(
      self, parser_mediator, query, row, **unused_kwargs):
    """Parses a zeitgeist event row.

    Args:
      parser_mediator (ParserMediator): mediates interactions between parsers
          and other components, such as storage and dfvfs.
      query (str): query that created the row.
      row (sqlite3.Row): row.
    """
    query_hash = hash(query)

    event_data = ZeitgeistActivityEventData()
    event_data.offset = self._GetRowValue(query_hash, row, 'id')
    event_data.query = query
    event_data.subject_uri = self._GetRowValue(query_hash, row, 'subj_uri')

    timestamp = self._GetRowValue(query_hash, row, 'timestamp')
    date_time = dfdatetime_java_time.JavaTime(timestamp=timestamp)
    event = time_events.DateTimeValuesEvent(
        date_time, definitions.TIME_DESCRIPTION_UNKNOWN)
    parser_mediator.ProduceEventWithEventData(event, event_data)


sqlite.SQLiteParser.RegisterPlugin(ZeitgeistActivityDatabasePlugin)
