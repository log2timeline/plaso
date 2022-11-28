# -*- coding: utf-8 -*-
"""SQLite parser plugin for MacOS TCC database files."""

from dfdatetime import posix_time as dfdatetime_posix_time

from plaso.containers import events
from plaso.parsers import sqlite
from plaso.parsers.sqlite_plugins import interface


class MacOSTCCEntry(events.EventData):
  """MacOS TCC event data.

  Attributes:
    allowed (bool): whether access to the service was allowed.
    client (str): name of the client requesting access to the service.
    modification_time (dfdatetime.DateTimeValues): date and time of the entry
        last modification.
    prompt_count (int): number of times an application prompted the user for
        access to a service.
    query (str): SQL query that was used to obtain the event data.
    service (str): name of the service.
  """

  DATA_TYPE = 'macos:tcc_entry'

  def __init__(self):
    """Initializes event data."""
    super(MacOSTCCEntry, self).__init__(data_type=self.DATA_TYPE)
    self.allowed = None
    self.client = None
    self.modification_time = None
    self.prompt_count = None
    self.query = None
    self.service = None


class MacOSTCCPlugin(interface.SQLitePlugin):
  """SQLite parser plugin for MacOS TCC database files.

  The MacOS Transparency, Consent, Control (TCC) database file is typically
  stored in:
  /Library/Application Support/com.apple.TCC/TCC.db
  /Users/<username>/Library/Application Support/com.apple.TCC/TCC.db
  """

  NAME = 'macostcc'
  DATA_FORMAT = (
      'MacOS Transparency, Consent, Control (TCC) SQLite database (TCC.db) '
      'file')

  REQUIRED_STRUCTURE = {
      'access': frozenset([
          'allowed', 'client', 'last_modified', 'prompt_count', 'service']),
      'access_overrides': frozenset([]),
      'active_policy': frozenset([]),
      'admin': frozenset([]),
      'expired': frozenset([]),
      'policies': frozenset([])}

  QUERIES = [(
      ('SELECT service, client, allowed, prompt_count, last_modified '
       'FROM access;'), 'ParseTCCEntry')]

  SCHEMAS = [{
      'access': (
          'CREATE TABLE access ( service TEXT NOT NULL, client TEXT NOT NULL, '
          'client_type INTEGER NOT NULL, allowed INTEGER NOT NULL, '
          'prompt_count INTEGER NOT NULL, csreq BLOB, policy_id INTEGER, '
          'indirect_object_identifier_type INTEGER, '
          'indirect_object_identifier TEXT, indirect_object_code_identity '
          'BLOB, flags INTEGER, last_modified INTEGER NOT NULL DEFAULT '
          '(CAST(strftime(\'%s\',\'now\') AS INTEGER)), PRIMARY KEY (service, '
          'client, client_type, indirect_object_identifier), FOREIGN KEY '
          '(policy_id) REFERENCES policies(id) ON DELETE CASCADE ON UPDATE '
          'CASCADE)'),
      'access_overrides': (
          'CREATE TABLE access_overrides ( service TEXT NOT NULL PRIMARY KEY)'),
      'active_policy': (
          'CREATE TABLE active_policy ( client TEXT NOT NULL, client_type '
          'INTEGER NOT NULL, policy_id INTEGER NOT NULL, PRIMARY KEY (client, '
          'client_type), FOREIGN KEY (policy_id) REFERENCES policies(id) ON '
          'DELETE CASCADE ON UPDATE CASCADE)'),
      'admin': (
          'CREATE TABLE admin (key TEXT PRIMARY KEY NOT NULL, value INTEGER '
          'NOT NULL)'),
      'expired': (
          'CREATE TABLE expired ( service TEXT NOT NULL, client TEXT NOT '
          'NULL, client_type INTEGER NOT NULL, csreq BLOB, last_modified '
          'INTEGER NOT NULL , expired_at INTEGER NOT NULL DEFAULT '
          '(CAST(strftime(\'%s\',\'now\') AS INTEGER)), PRIMARY KEY (service, '
          'client, client_type))'),
      'policies': (
          'CREATE TABLE policies ( id INTEGER NOT NULL PRIMARY KEY, bundle_id '
          'TEXT NOT NULL, uuid TEXT NOT NULL, display TEXT NOT NULL, UNIQUE '
          '(bundle_id, uuid))')}]

  def _GetDateTimeRowValue(self, query_hash, row, value_name):
    """Retrieves a date and time value from the row.

    Args:
      query_hash (int): hash of the query, that uniquely identifies the query
          that produced the row.
      row (sqlite3.Row): row.
      value_name (str): name of the value.

    Returns:
      dfdatetime.PosixTime: date and time value or None if not available.
    """
    timestamp = self._GetRowValue(query_hash, row, value_name)
    if timestamp is None:
      return None

    return dfdatetime_posix_time.PosixTime(timestamp=timestamp)

  def ParseTCCEntry(self, parser_mediator, query, row, **unused_kwargs):
    """Parses an application usage row.

    Args:
      parser_mediator (ParserMediator): mediates interactions between parsers
          and other components, such as storage and dfVFS.
      query (str): query that created the row.
      row (sqlite3.Row): row.
    """
    query_hash = hash(query)

    event_data = MacOSTCCEntry()
    event_data.allowed = self._GetRowValue(query_hash, row, 'allowed')
    event_data.client = self._GetRowValue(query_hash, row, 'client')
    event_data.modification_time = self._GetDateTimeRowValue(
        query_hash, row, 'last_modified')
    event_data.prompt_count = self._GetRowValue(query_hash, row, 'prompt_count')
    event_data.query = query
    event_data.service = self._GetRowValue(query_hash, row, 'service')

    parser_mediator.ProduceEventData(event_data)


sqlite.SQLiteParser.RegisterPlugin(MacOSTCCPlugin)
