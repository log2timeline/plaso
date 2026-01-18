# -*- coding: utf-8 -*-
"""SQLite parser plugin for Health Workouts database on iOS."""

from dfdatetime import cocoa_time as dfdatetime_cocoa_time

from plaso.containers import events
from plaso.parsers import sqlite
from plaso.parsers.sqlite_plugins import interface


class IOSHealthWorkoutsEventData(events.EventData):
  """iOS Health workouts event data.

  Attributes:
    activity_type (str): workout activity type.
    date_time (dfdatetime.DateTimeValues): primary timestamp for timeline.
    duration (float): duration in seconds (raw from DB).
    duration_in_minutes (float): duration in minutes.
    end_date (dfdatetime.DateTimeValues): Cocoa time end date.
    end_date_str (str): ISO/RFC3339 timestamp string from end_date.
    goal (str): workout goal value.
    goal_type (str): workout goal type.
    start_date (dfdatetime.DateTimeValues): Cocoa time start date.
    start_date_str (str): ISO/RFC3339 timestamp string from start_date.
    total_basal_energy_burned (float): basal energy (kcal).
    total_distance_km (float): distance in kilometers.
    total_distance_miles (float): distance in miles.
    total_energy_burned (float): active energy (kcal).
    total_flights_climbed (float): flights climbed total.
    total_w_steps (float): steps total.
    workout_duration (str): 'HH:MM:SS' derived from duration.
  """

  DATA_TYPE = 'ios:health:workouts'

  def __init__(self):
    """Initializes event data."""
    super(IOSHealthWorkoutsEventData, self).__init__(data_type=self.DATA_TYPE)
    self.activity_type = None
    self.date_time = None
    self.duration = None
    self.duration_in_minutes = None
    self.end_date = None
    self.end_date_str = None
    self.goal = None
    self.goal_type = None
    self.start_date = None
    self.start_date_str = None
    self.total_basal_energy_burned = None
    self.total_distance_km = None
    self.total_distance_miles = None
    self.total_energy_burned = None
    self.total_flights_climbed = None
    self.total_w_steps = None
    self.workout_duration = None


class IOSHealthWorkoutsPlugin(interface.SQLitePlugin):
  """SQLite parser plugin for Health Workouts database on iOS."""

  NAME = 'ios_health_workouts'
  DATA_FORMAT = (
      'iOS Health Workouts SQLite database file healthdb_secure.sqlite')

  REQUIRED_STRUCTURE = {
      'workouts': frozenset([
          'activity_type', 'duration', 'total_distance',
          'total_energy_burned', 'total_basal_energy_burned',
          'goal_type', 'goal', 'total_flights_climbed', 'total_w_steps']),
      'samples': frozenset([
          'data_id', 'start_date', 'end_date'])}

  QUERIES = [((
      'SELECT samples.start_date AS start_date, samples.end_date AS end_date, '
      'workouts.activity_type AS activity_type, workouts.duration AS duration, '
      'workouts.total_distance AS total_distance, '
      'workouts.total_energy_burned AS total_energy_burned, '
      'workouts.total_basal_energy_burned AS total_basal_energy_burned, '
      'workouts.goal_type AS goal_type, workouts.goal AS goal, '
      'workouts.total_flights_climbed AS total_flights_climbed, '
      'workouts.total_w_steps AS total_w_steps FROM workouts LEFT JOIN '
      'samples ON samples.data_id = workouts.data_id GROUP BY workouts.data_id '
      'ORDER BY samples.start_date'),
      'ParseWorkoutRow')]

  SCHEMAS = {
      'workouts': (
          'CREATE TABLE workouts (data_id INTEGER PRIMARY KEY, activity_type '
          'TEXT, duration REAL, total_distance REAL, total_energy_burned REAL, '
          'total_basal_energy_burned REAL, goal_type TEXT, goal TEXT, '
          'total_flights_climbed REAL, total_w_steps REAL)'),
      'samples': (
          'CREATE TABLE samples (data_id INTEGER PRIMARY KEY, start_date '
          'INTEGER, end_date INTEGER)')}

  REQUIRE_SCHEMA_MATCH = False

  def _GetDateTimeRowValue(self, query_hash, row, value_name):
    """Retrieves a Cocoa DateTime value from the row.

    Args:
      query_hash (int): hash of the query.
      row (sqlite3.Row): row.
      value_name (str): name of the value.

    Returns:
      dfdatetime.CocoaTime: date and time value or None.
    """
    timestamp = self._GetRowValue(query_hash, row, value_name)
    if timestamp is None:
      return None
    return dfdatetime_cocoa_time.CocoaTime(timestamp=timestamp)

  def _CopyToRfc3339String(self, dfdt):
    """Returns RFC3339/ISO string from a dfdatetime object.

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

  def _SecondsToHMS(self, seconds_value):
    """Converts seconds to 'HH:MM:SS'.

    Args:
      seconds_value (float|int): duration in seconds.

    Returns:
      str: duration in HH:MM:SS or None.
    """
    try:
      total = int(float(seconds_value))
    except (TypeError, ValueError):
      return None
    hours = total // 3600
    minutes = (total % 3600) // 60
    seconds = total % 60
    return f'{hours:02d}:{minutes:02d}:{seconds:02d}'

  def _DistanceToKmMiles(self, total_distance):
    """Converts distance to (km, miles).

    Args:
      total_distance (float): distance value.

    Returns:
      tuple: (kilometers, miles).
    """
    try:
      km = float(total_distance)
    except (TypeError, ValueError):
      return None, None

    miles = km * 0.621371
    return km, miles

  def ParseWorkoutRow(self, parser_mediator, query, row, **unused_kwargs):
    """Parses a workout row.

    Args:
      parser_mediator (ParserMediator): mediates interactions.
      query (str): query that created the row.
      row (sqlite3.Row): row.
    """
    query_hash = hash(query)
    event_data = IOSHealthWorkoutsEventData()

    event_data.start_date = self._GetDateTimeRowValue(
        query_hash, row, 'start_date')
    event_data.end_date = self._GetDateTimeRowValue(
        query_hash, row, 'end_date')
    event_data.start_date_str = self._CopyToRfc3339String(event_data.start_date)
    event_data.end_date_str = self._CopyToRfc3339String(event_data.end_date)
    event_data.date_time = event_data.start_date
    event_data.activity_type = self._GetRowValue(
        query_hash, row, 'activity_type')

    duration_seconds = self._GetRowValue(query_hash, row, 'duration')
    event_data.duration = duration_seconds
    event_data.workout_duration = self._SecondsToHMS(duration_seconds)

    if duration_seconds is not None:
      try:
        event_data.duration_in_minutes = float(duration_seconds) / 60.0
      except (TypeError, ValueError):
        event_data.duration_in_minutes = None

    total_distance = self._GetRowValue(query_hash, row, 'total_distance')
    km_val, miles_val = self._DistanceToKmMiles(total_distance)
    event_data.total_distance_km = km_val
    event_data.total_distance_miles = miles_val

    event_data.total_energy_burned = self._GetRowValue(
        query_hash, row, 'total_energy_burned')
    event_data.total_basal_energy_burned = self._GetRowValue(
        query_hash, row, 'total_basal_energy_burned')
    event_data.goal_type = self._GetRowValue(query_hash, row, 'goal_type')
    event_data.goal = self._GetRowValue(query_hash, row, 'goal')
    event_data.total_flights_climbed = self._GetRowValue(
        query_hash, row, 'total_flights_climbed')
    event_data.total_w_steps = self._GetRowValue(
        query_hash, row, 'total_w_steps')

    parser_mediator.ProduceEventData(event_data)


sqlite.SQLiteParser.RegisterPlugin(IOSHealthWorkoutsPlugin)
