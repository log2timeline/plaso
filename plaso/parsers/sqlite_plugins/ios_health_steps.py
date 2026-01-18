# -*- coding: utf-8 -*-
"""SQLite parser plugin for iOS Health Steps database."""

from dfdatetime import cocoa_time as dfdatetime_cocoa_time

from plaso.containers import events
from plaso.parsers import sqlite
from plaso.parsers.sqlite_plugins import interface


class IOSHealthStepsEventData(events.EventData):
  """iOS Health Steps event data.

  Attributes:
    date_time (dfdatetime.DateTimeValues): primary timestamp for timeline.
    device (str): device used to record the data (e.g. Apple Watch).
    duration (float): duration in seconds.
    end_date (dfdatetime.DateTimeValues): Cocoa time end date.
    end_date_str (str): ISO/RFC3339 timestamp string from end_date.
    start_date (dfdatetime.DateTimeValues): Cocoa time start date.
    start_date_str (str): ISO/RFC3339 timestamp string from start_date.
    steps (int): total number of steps.
  """

  DATA_TYPE = 'ios:health:steps'

  def __init__(self):
    """Initializes event data."""
    super(IOSHealthStepsEventData, self).__init__(data_type=self.DATA_TYPE)
    self.date_time = None
    self.device = None
    self.duration = None
    self.end_date = None
    self.end_date_str = None
    self.start_date = None
    self.start_date_str = None
    self.steps = None


class IOSHealthStepsPlugin(interface.SQLitePlugin):
  """SQLite parser plugin for iOS Health Steps database."""

  NAME = 'ios_health_steps'
  DATA_FORMAT = (
      'iOS Health Steps SQLite database file healthdb_secure.sqlite')

  REQUIRED_STRUCTURE = {
      'samples': frozenset(['data_id', 'start_date', 'end_date']),
      'quantity_samples': frozenset(['quantity']),
      'data_provenances': frozenset(['origin_product_type']),
      'objects': frozenset(['data_id'])}

  QUERIES = [((
      'SELECT samples.start_date AS start_date, samples.end_date AS end_date, '
      'quantity_samples.quantity AS steps, '
      'data_provenances.origin_product_type AS device FROM samples '
      'LEFT JOIN quantity_samples ON samples.data_id = '
      'quantity_samples.data_id LEFT JOIN objects ON samples.data_id = '
      'objects.data_id LEFT JOIN data_provenances ON objects.provenance = '
      'data_provenances.rowid WHERE samples.data_type = 7 AND '
      'quantity_samples.quantity IS NOT NULL ORDER BY '
      'samples.start_date DESC'),
      'ParseStepsRow')]

  def _GetDateTimeRowValue(self, query_hash, row, value_name):
    """Retrieves a Cocoa DateTime value from the row.

    Args:
      query_hash (int): hash of the query.
      row (sqlite3.Row): row.
      value_name (str): name of the value.

    Returns:
      dfdatetime.CocoaTime: date and time value or None if not available.
    """
    timestamp = self._GetRowValue(query_hash, row, value_name)
    if timestamp is None:
      return None
    return dfdatetime_cocoa_time.CocoaTime(timestamp=timestamp)

  def _CopyToRfc3339String(self, dfdt):
    """Returns RFC3339/ISO string from a dfdatetime object or None.

    Args:
      dfdt (dfdatetime.DateTimeValues): date time value.

    Returns:
      str: formatted date time string or None.
    """
    if dfdt is None:
      return None
    try:
      to_rfc3339 = getattr(dfdt, 'CopyToDateTimeStringRFC3339', None)
      if callable(to_rfc3339):
        return to_rfc3339()
      return dfdt.CopyToDateTimeString()
    except (AttributeError, TypeError, ValueError):
      return None

  def ParseStepsRow(self, parser_mediator, query, row, **unused_kwargs):
    """Parses a steps row.

    Args:
      parser_mediator (ParserMediator): mediates interactions between parsers.
      query (str): query that created the row.
      row (sqlite3.Row): row.
    """
    query_hash = hash(query)
    event_data = IOSHealthStepsEventData()

    event_data.start_date = self._GetDateTimeRowValue(
        query_hash, row, 'start_date')
    event_data.end_date = self._GetDateTimeRowValue(
        query_hash, row, 'end_date')
    event_data.start_date_str = self._CopyToRfc3339String(event_data.start_date)
    event_data.end_date_str = self._CopyToRfc3339String(event_data.end_date)
    event_data.date_time = event_data.start_date
    event_data.steps = self._GetRowValue(query_hash, row, 'steps')
    event_data.device = self._GetRowValue(query_hash, row, 'device')

    if event_data.start_date and event_data.end_date:
      try:
        event_data.duration = (
            event_data.end_date.timestamp - event_data.start_date.timestamp)
      except (AttributeError, TypeError):
        event_data.duration = None

    parser_mediator.ProduceEventData(event_data)


sqlite.SQLiteParser.RegisterPlugin(IOSHealthStepsPlugin)
