# -*- coding: utf-8 -*-
"""SQLite parser plugin for Windows Diagnosis EventTranscript database file."""

import json

from dfdatetime import filetime as dfdatetime_filetime

from plaso.containers import events
from plaso.parsers import sqlite
from plaso.parsers.sqlite_plugins import interface


class WindowsEventTranscriptEventData(events.EventData):
  """Windows diagnosis EventTranscript event data.

  Attributes:
    application_name (str): Application name.
    application_root_directory (str): Application root directory.
    application_version (str): Application version.
    compressed_payload_size (int): Size of the compressed payload.
    event_keywords (int): Event keywords
    event_name_hash (int): Hash of full event name.
    event_name (str): Diagnosis full event name.
    friendly_logging_binary_name (str): Friendly name for logging binary.
    ikey (str): iKey
    is_core (int): Boolean value represented as an integer.
    logging_binary_name (str): Binary that generated the event.
    name (str): Name of the payload, similar to event name.
    producer_identifier (int): Identifier of the EventTranscript event producer.
        provider group.
    provider_group_identifier (int): Identifier of the EventTranscript event
    recorded_time (dfdatetime.DateTimeValues): date and time the entry
        was recorded.
    user_identifier (str): Windows Security identifier (SID) of a user account.
    version (str): Payload version
  """

  DATA_TYPE = 'windows:diagnosis:eventtranscript'

  def __init__(self):
    """Initializes event data."""
    super(WindowsEventTranscriptEventData, self).__init__(
        data_type=self.DATA_TYPE)
    self.application_name = None
    self.application_root_directory = None
    self.application_version = None
    self.compressed_payload_size = None
    self.event_keywords = None
    self.event_name_hash = None
    self.event_name = None
    self.friendly_logging_binary_name = None
    self.ikey = None
    self.is_core = None
    self.logging_binary_name = None
    self.name = None
    self.producer_identifier = None
    self.provider_group_identifier = None
    self.recorded_time = None
    self.user_identifier = None
    self.version = None


class EventTranscriptPlugin(interface.SQLitePlugin):
  """SQLite parser plugin for Windows diagnosis EventTranscript database files.

  The Windows diagnosis EventTranscript database file is typically stored in:
  EventTranscript.db
  """

  NAME = 'windows_eventtranscript'
  DATA_FORMAT = (
      'Windows diagnosis EventTranscript SQLite database (EventTranscript.db) '
      'file')

  REQUIRED_STRUCTURE = {
      'events_persisted': frozenset([
          'sid',
          'timestamp',
          'payload',
          'full_event_name',
          'full_event_name_hash',
          'event_keywords',
          'is_core',
          'provider_group_id',
          'logging_binary_name',
          'friendly_logging_binary_name',
          'compressed_payload_size',
          'producer_id'])}

  QUERIES = [
      (('SELECT events_persisted.sid,'
        'events_persisted.timestamp,'
        'events_persisted.payload,'
        'events_persisted.full_event_name,'
        'events_persisted.full_event_name_hash,'
        'events_persisted.event_keywords,'
        'events_persisted.is_core,'
        'events_persisted.provider_group_id,'
        'events_persisted.logging_binary_name,'
        'events_persisted.friendly_logging_binary_name,'
        'events_persisted.compressed_payload_size,'
        'events_persisted.producer_id '
        'from events_persisted'),
        'ParseEventTranscriptRow')]

  SCHEMAS = [{
      'events_persisted': (
          'CREATE TABLE events_persisted ('
          'sid TEXT,'
          'timestamp INTEGER,'
          'payload TEXT,'
          'full_event_name TEXT,'
          'full_event_name_hash INTEGER,'
          'event_keywords INTEGER,'
          'is_core INTEGER, '
          'provider_group_id INTEGER,'
          'logging_binary_name TEXT,'
          'friendly_logging_binary_name TEXT, '
          'compressed_payload_size INTEGER,'
          'producer_id INTEGER,'
          'extra1 TEXT, '
          'extra2 TEXT,'
          'extra3 TEXT,'
          'FOREIGN KEY(provider_group_id) '
          'REFERENCES provider_groups(group_id), '
          'CONSTRAINT fk_producer_id '
          'FOREIGN KEY(producer_id) '
          'REFERENCES producers(producer_id) ON DELETE CASCADE)')}]

  def _GetDateTimeRowValue(self, query_hash, row, value_name):
    """Retrieves a date and time value from the row.

    Args:
      query_hash (int): hash of the query, that uniquely identifies the query
          that produced the row.
      row (sqlite3.Row): row.
      value_name (str): name of the value.

    Returns:
      dfdatetime.Filetime: date and time value or None if not available.
    """
    timestamp = self._GetRowValue(query_hash, row, value_name)
    if timestamp is None:
      return None

    return dfdatetime_filetime.Filetime(timestamp=timestamp)

  def ParseEventTranscriptRow(
      self, parser_mediator, query, row, **unused_kwargs):
    """Parses EventTranscript row.

    Args:
      parser_mediator (ParserMediator): mediates interactions between parsers
          and other components, such as storage and dfVFS.
      query (str): query that created the row.
      row (sqlite3.Row): row.
    """
    query_hash = hash(query)

    event_data = WindowsEventTranscriptEventData()
    event_data.compressed_payload_size = self._GetRowValue(
        query_hash, row, 'compressed_payload_size')
    event_data.event_keywords = self._GetRowValue(
        query_hash, row, 'event_keywords')
    event_data.event_name = self._GetRowValue(
        query_hash, row, 'full_event_name')
    event_data.event_name_hash = self._GetRowValue(
        query_hash, row, 'full_event_name_hash')
    event_data.friendly_logging_binary_name = self._GetRowValue(
        query_hash, row, 'friendly_logging_binary_name')
    event_data.is_core = self._GetRowValue(
        query_hash, row, 'is_core')
    event_data.logging_binary_name = self._GetRowValue(
        query_hash, row, 'logging_binary_name')
    event_data.producer_identifier = self._GetRowValue(
        query_hash, row, 'producer_id')
    event_data.provider_group_identifier = self._GetRowValue(
        query_hash, row, 'provider_group_id')
    event_data.recorded_time = self._GetDateTimeRowValue(
        query_hash, row, 'timestamp')
    # If the user identifier is an empty string set it to None.
    event_data.user_identifier = self._GetRowValue(
        query_hash, row, 'sid') or None

    # Parse the payload.
    payload = json.loads(self._GetRowValue(query_hash, row, 'payload'))
    payload_data = payload['data']
    payload_name = payload['name']

    event_data.ikey = payload['iKey']
    event_data.name = payload_name
    event_data.version = payload['ver']

    # TODO: add support for
    # data = json.dumps(payload_data, separators=(',',':'))
    # extension = json.dumps(payload['ext'], separators=(',',':'))

    # Microsoft.Windows.Inventory.Core.InventoryApplicationAdd
    if payload_name == (
        'Microsoft.Windows.Inventory.Core.InventoryApplicationAdd'):
      event_data.application_name = payload_data['Name']
      event_data.application_version = payload_data['Version']
      event_data.application_root_directory = payload_data['RootDirPath']

      # TODO: generate event for: payload_data['InstallDate']

    # Win32kTraceLogging.AppInteractivitySummary
    elif payload_name == 'Win32kTraceLogging.AppInteractivitySummary':
      event_data.application_version = payload_data['AppVersion']

    # TODO: generate event for: payload['time']

    parser_mediator.ProduceEventData(event_data)


sqlite.SQLiteParser.RegisterPlugin(EventTranscriptPlugin)
