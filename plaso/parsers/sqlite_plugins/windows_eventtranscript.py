# -*- coding: utf-8 -*-
"""SQLite parser plugin for Windows Diagnosis EventTranscript database file."""
import json

from dfdatetime import filetime as dfdatetime_filetime

from plaso.containers import events
from plaso.containers import time_events
from plaso.lib import definitions
from plaso.parsers import sqlite
from plaso.parsers.sqlite_plugins import interface


class EventTranscriptEventData(events.EventData):
  """Windows diagnosis EventTranscript event data.

  Attributes:
    sid (str): Windows Security ID of a user account.
    timestamp (int): Event timestamp in UTC
    raw_payload (str): JSON payload specific to event name
    full_event_name (str): Diagnosis full event name.
    full_event_name_hash (int): Hash of full event name.
    event_keywords (int): Event keywords
    is_core (int): Boolean value represted as integer.
    provider_group_id (int): Provider group ID.
    logging_binary_name (str): Binary that generated the event.
    friendly_logging_binary_name (str): Friendly name for logging binary.
    compressed_payload_size (int): Size of compressed payload.
    producer_id (int): Producer ID.
    description (str): Tag description

    The section below contains partially parsed payload data.
    ver (str): Payload version
    name (str): Name of the event. This contains the same information as
        full_event_name.
    time (str): Timestamp of the event as string in UTC. This is the same time
        recorded in timestamp field.
    ikey (str): iKey
    ext (str): This field contains the additional information about the event.
        The information is JSON document stored as string.
    data (str): This field contains the important information about the event.
        The field contains JSON data stored as string. Due to the dynamic nature
        of the data, extracting field is not practicle.

    # This section contains selective fields extracted from payload data field.
    app_name (str): Application name.
    app_version (str): Applciation version.
    app_root_dir_path (str): Application root directory.
    app_install_date (str): Application installed date.
  """

  DATA_TYPE = 'windows:diagnosis:eventtranscript'

  def __init__(self):
    """Initializes event data."""
    super(EventTranscriptEventData, self).__init__(data_type=self.DATA_TYPE)
    self.sid = None
    self.timestamp = None
    self.raw_payload = None
    self.full_event_name = None
    self.full_event_name_hash = None
    self.event_keywords = None
    self.is_core = None
    self.provider_group_id = None
    self.logging_binary_name = None
    self.friendly_logging_binary_name = None
    self.compressed_payload_size = None
    self.producer_id = None

    # Fields extracted from payload structure
    self.ver = None
    self.name = None
    self.time = None
    self.ikey = None
    self.ext = None
    self.data = None

    # The fields below are extracted from the diagnosis events
    # - Microsoft.Windows.Inventory.Core.InventoryApplicationAdd
    # - Win32kTraceLogging.AppInteractivitySummary
    self.app_name = None
    self.app_version = None
    self.app_root_dir_path = None
    self.app_install_date = None


class EventTranscriptPlugin(interface.SQLitePlugin):
  """SQLite parser plugin for Windows diagnosis EventTranscript database files.

  The Windows diagnosis EventTranscript database file is typically stored in:
  EventTranscript.db
  """

  NAME = 'windows:diagnosis:eventtranscript'
  DATA_FORMAT = (
      'Windows diagnosis EventTranscript SQLite database (EventTranscript.db)'
      ' file')

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
        'producer_id'
      ])}

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

  def ParseEventTranscriptRow(
      self, parser_mediator, query, row, **unused_kwargs):
    """Parses EventTranscript row.

    Args:
      parser_mediator (ParserMediator): mediates interactions between parsers
          and other components, such as storage and dfvfs.
      query (str): query that created the row.
      row (sqlite3.Row): row.
    """
    query_hash = hash(query)

    event_data = EventTranscriptEventData()
    event_data.sid = self._GetRowValue(
        query_hash, row, 'sid')
    event_data.raw_payload = self._GetRowValue(
        query_hash, row, 'payload')
    event_data.full_event_name = self._GetRowValue(
        query_hash, row, 'full_event_name')
    event_data.full_event_name_hash = self._GetRowValue(
        query_hash, row, 'full_event_name_hash')
    event_data.event_keywords = self._GetRowValue(
        query_hash, row, 'event_keywords')
    event_data.is_core = self._GetRowValue(
        query_hash, row, 'is_core')
    event_data.provider_group_id = self._GetRowValue(
        query_hash, row, 'provider_group_id')
    event_data.logging_binary_name = self._GetRowValue(
        query_hash, row, 'logging_binary_name')
    event_data.friendly_logging_binary_name = self._GetRowValue(
        query_hash, row, 'friendly_logging_binary_name')
    event_data.compressed_payload_size = self._GetRowValue(
        query_hash, row, 'compressed_payload_size')
    event_data.producer_id = self._GetRowValue(
        query_hash, row, 'producer_id')

    # Parse raw_payload
    payload = json.loads(self._GetRowValue(
        query_hash, row, 'payload'))
    event_data.ver = payload['ver']
    event_data.name = payload['name']
    event_data.time = payload['time']
    event_data.ikey = payload['iKey']
    event_data.ext = json.dumps(payload['ext'], separators=(',',':'))
    event_data.data = json.dumps(payload['data'], separators=(',',':'))

    # Parse payload for key fields
    # Microsoft.Windows.Inventory.Core.InventoryApplicationAdd
    if payload['name'] == '''Microsoft.Windows.
Inventory.Core.InventoryApplicationAdd''':
      event_data.app_name = payload['data']['Name']
      event_data.app_version = payload['data']['Version']
      event_data.app_root_dir_path = payload['data']['RootDirPath']
      event_data.app_install_date = payload['data']['InstallDate']

    # Win32kTraceLogging.AppInteractivitySummary
    if payload['name'] == 'Win32kTraceLogging.AppInteractivitySummary':
      event_data.app_version = payload['data']['AppVersion']

    timestamp = self._GetRowValue(
        query_hash, row, 'timestamp')
    if timestamp:
      date_time = dfdatetime_filetime.Filetime(
          timestamp=timestamp)
      event = time_events.DateTimeValuesEvent(
          date_time, definitions.TIME_DESCRIPTION_RECORDED)
      parser_mediator.ProduceEventWithEventData(event, event_data)


sqlite.SQLiteParser.RegisterPlugin(EventTranscriptPlugin)
