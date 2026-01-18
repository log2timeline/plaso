# -*- coding: utf-8 -*-
"""SQLite parser plugin for iOS Health Resting Heart Rate database."""

from dfdatetime import cocoa_time as dfdatetime_cocoa_time

from plaso.containers import events
from plaso.parsers import sqlite
from plaso.parsers.sqlite_plugins import interface


class IOSHealthRestingHeartRateEventData(events.EventData):
  """iOS Health resting heart rate event data.

  Attributes:
    date_added_to_health (dfdatetime.DateTimeValues): when added to Health.
    date_added_to_health_str (str): rendered added date for YAML formatter.
    date_time (dfdatetime.DateTimeValues): primary timestamp (start).
    end_date (dfdatetime.DateTimeValues): Cocoa time (sec since 2001-01-01).
    end_date_str (str): rendered end_date for YAML formatter.
    hardware (str): device hardware.
    resting_heart_rate (int): BPM.
    source (str): source name.
    start_date (dfdatetime.DateTimeValues): Cocoa time (sec since 2001-01-01).
    start_date_str (str): rendered start_date for YAML formatter.
  """

  DATA_TYPE = 'ios:health:resting_heart_rate'

  def __init__(self):
    """Initializes event data."""
    super(IOSHealthRestingHeartRateEventData, self).__init__(
        data_type=self.DATA_TYPE)
    self.date_added_to_health = None
    self.date_added_to_health_str = None
    self.date_time = None
    self.end_date = None
    self.end_date_str = None
    self.hardware = None
    self.resting_heart_rate = None
    self.source = None
    self.start_date = None
    self.start_date_str = None


class IOSHealthRestingHeartRatePlugin(interface.SQLitePlugin):
  """SQLite parser plugin for iOS Health Resting Heart Rate database."""

  NAME = 'ios_health_resting_heart_rate'
  DATA_FORMAT = (
      'iOS Health Resting Heart Rate SQLite database file '
      'healthdb_secure.sqlite')

  REQUIRED_STRUCTURE = {
      'samples': frozenset(['data_id', 'start_date', 'end_date', 'data_type']),
      'quantity_samples': frozenset(['data_id', 'quantity']),
      'objects': frozenset(['data_id', 'creation_date', 'provenance']),
      'data_provenances': frozenset(['ROWID', 'source_id']),
      'sources': frozenset(['ROWID', 'product_type', 'name'])}

  QUERIES = [((
      'SELECT samples.start_date AS start_date, samples.end_date AS end_date, '
      'CAST(ROUND(quantity_samples.quantity) AS INTEGER) AS '
      'resting_heart_rate, objects.creation_date AS date_added_to_health, '
      'sources.product_type AS hardware, sources.name AS source FROM samples '
      'LEFT JOIN quantity_samples ON samples.data_id = '
      'quantity_samples.data_id LEFT JOIN objects ON samples.data_id = '
      'objects.data_id LEFT JOIN data_provenances ON objects.provenance = '
      'data_provenances.ROWID LEFT JOIN sources ON '
      'data_provenances.source_id = sources.ROWID WHERE '
      'samples.data_type = 118 AND quantity_samples.quantity IS NOT NULL '
      'ORDER BY samples.start_date DESC'),
      'ParseRestingHeartRateRow')]

  def _ParseDateTime(self, timestamp):
    """Return a dfdatetime CocoaTime object (or None).

    Args:
      timestamp (float): Cocoa Time timestamp.

    Returns:
      dfdatetime.CocoaTime: date and time value or None.
    """
    if timestamp is None:
      return None
    try:
      return dfdatetime_cocoa_time.CocoaTime(timestamp=timestamp)
    except (TypeError, ValueError):
      return None

  def ParseRestingHeartRateRow(
      self, parser_mediator, query, row, **unused_kwargs):
    """Parses a resting heart rate row.

    Args:
      parser_mediator (ParserMediator): mediates interactions.
      query (str): query that created the row.
      row (sqlite3.Row): row.
    """
    query_hash = hash(query)
    event_data = IOSHealthRestingHeartRateEventData()

    start_ts = self._GetRowValue(query_hash, row, 'start_date')
    end_ts = self._GetRowValue(query_hash, row, 'end_date')
    created_ts = self._GetRowValue(query_hash, row, 'date_added_to_health')

    event_data.start_date = self._ParseDateTime(start_ts)
    event_data.end_date = self._ParseDateTime(end_ts)
    event_data.date_added_to_health = self._ParseDateTime(created_ts)
    event_data.date_time = event_data.start_date

    if event_data.start_date:
      event_data.start_date_str = event_data.start_date.CopyToDateTimeString()
    if event_data.end_date:
      event_data.end_date_str = event_data.end_date.CopyToDateTimeString()
    if event_data.date_added_to_health:
      dt_added = event_data.date_added_to_health
      event_data.date_added_to_health_str = dt_added.CopyToDateTimeString()

    event_data.resting_heart_rate = self._GetRowValue(
        query_hash, row, 'resting_heart_rate')
    event_data.hardware = self._GetRowValue(query_hash, row, 'hardware')
    event_data.source = self._GetRowValue(query_hash, row, 'source')

    parser_mediator.ProduceEventData(event_data)


sqlite.SQLiteParser.RegisterPlugin(IOSHealthRestingHeartRatePlugin)
