# -*- coding: utf-8 -*-
"""SQLite parser plugin for Health Workouts (iOS 16/17)."""

from dfdatetime import cocoa_time as dfdatetime_cocoa_time

from plaso.containers import events
from plaso.parsers import sqlite
from plaso.parsers.sqlite_plugins import interface


class IOSHealthWorkoutsLatestEventData(events.EventData):
  """iOS 16/17 Health workouts (workout_activities) event data.

  Attributes:
    activity_type (int): RAW code from workout_activities.activity_type.
    added_timestamp (dfdatetime.DateTimeValues): when workout was added.
    added_timestamp_str (str): rendered added timestamp.
    average_mets (float): average METs value.
    avg_heart_rate_bpm (int): average heart rate in BPM.
    core_duration (float): duration spent in core sleep (if applicable).
    date_time (dfdatetime.DateTimeValues): primary timestamp (start).
    duration_in_minutes (float): duration_seconds / 60.
    end_date (dfdatetime.DateTimeValues): Cocoa time end date.
    end_date_str (str): RFC3339 string from end_date.
    goal (str): workout goal value.
    goal_type (int): RAW code from workouts.goal_type.
    hardware (str): source_devices.hardware.
    humidity_percent (int): weather humidity.
    latitude (float): weather location latitude.
    location_type (int): RAW code from workout_activities.location_type.
    longitude (float): weather location longitude.
    max_ground_elevation_m (float): maximum ground elevation.
    max_heart_rate_bpm (int): maximum heart rate in BPM.
    min_ground_elevation_m (float): minimum ground elevation.
    min_heart_rate_bpm (int): minimum heart rate in BPM.
    software_version (str): data_provenances.source_version.
    source (str): sources.name.
    start_date (dfdatetime.DateTimeValues): Cocoa time start date.
    start_date_str (str): RFC3339 string from start_date.
    temperature_c (float): temperature in Celsius.
    temperature_f (float): temperature in Fahrenheit.
    timezone (str): data_provenances.tz_name.
    total_active_energy_kcal (float): active energy burned.
    total_distance_km (float): distance in kilometers.
    total_distance_miles (float): distance in miles.
    total_resting_energy_kcal (float): resting energy burned.
    total_time_duration (str): HH:MM:SS (samples.end - samples.start).
    workout_duration (str): HH:MM:SS from duration seconds.
  """

  DATA_TYPE = 'ios:health:workouts_latest'

  def __init__(self):
    """Initializes event data."""
    super(IOSHealthWorkoutsLatestEventData, self).__init__(
        data_type=self.DATA_TYPE)
    self.activity_type = None
    self.added_timestamp = None
    self.added_timestamp_str = None
    self.average_mets = None
    self.avg_heart_rate_bpm = None
    self.date_time = None
    self.duration_in_minutes = None
    self.end_date = None
    self.end_date_str = None
    self.goal = None
    self.goal_type = None
    self.hardware = None
    self.humidity_percent = None
    self.latitude = None
    self.location_type = None
    self.longitude = None
    self.max_ground_elevation_m = None
    self.max_heart_rate_bpm = None
    self.min_ground_elevation_m = None
    self.min_heart_rate_bpm = None
    self.software_version = None
    self.source = None
    self.start_date = None
    self.start_date_str = None
    self.temperature_c = None
    self.temperature_f = None
    self.timezone = None
    self.total_active_energy_kcal = None
    self.total_distance_km = None
    self.total_distance_miles = None
    self.total_resting_energy_kcal = None
    self.total_time_duration = None
    self.workout_duration = None


class IOSHealthWorkoutsLatestPlugin(interface.SQLitePlugin):
  """SQLite parser plugin for Health Workouts (iOS 16/17)."""

  NAME = 'ios_health_workouts_latest'
  DATA_FORMAT = (
      'iOS Health Workouts (iOS 16/17) workout_activities schema in '
      'healthdb_secure.sqlite')

  REQUIRED_STRUCTURE = {
      'workout_activities': frozenset([
          'ROWID', 'owner_id', 'activity_type', 'start_date', 'end_date',
          'duration', 'location_type']),
      'samples': frozenset(['data_id', 'start_date', 'end_date']),
      'workouts': frozenset(['data_id', 'total_distance', 'goal_type', 'goal']),
      'workout_statistics': frozenset([
          'workout_activity_id', 'data_type', 'quantity']),
      'metadata_keys': frozenset(['ROWID', 'key']),
      'metadata_values': frozenset([
          'object_id', 'key_id', 'numerical_value', 'string_value']),
      'objects': frozenset(['data_id', 'creation_date', 'provenance']),
      'data_provenances': frozenset([
          'ROWID', 'source_version', 'tz_name', 'device_id', 'source_id']),
      'source_devices': frozenset(['ROWID', 'hardware']),
      'sources': frozenset(['ROWID', 'name'])}

  QUERIES = [((
      'SELECT wa.start_date AS start_cocoa, wa.end_date AS end_cocoa, '
      'wa.activity_type AS activity_type_code, wa.location_type AS '
      'location_type_code, wa.duration AS duration_seconds, s.start_date AS '
      'sample_start_cocoa, s.end_date AS sample_end_cocoa, w.total_distance '
      'AS total_distance_km, w.goal_type AS goal_type_code, w.goal AS '
      'goal_value, MAX(CASE WHEN ws.data_type = 10 THEN ROUND(ws.quantity, 2) '
      'END) AS total_active_kcal, MAX(CASE WHEN ws.data_type = 9 THEN '
      'ROUND(ws.quantity, 2) END) AS total_resting_kcal, MAX(CASE WHEN '
      'mk.key="HKAverageMETs" THEN ROUND(mv.numerical_value,1) END) AS '
      'avg_mets, MAX(CASE WHEN mk.key="_HKPrivateWorkoutMinHeartRate" THEN '
      'CAST(ROUND(mv.numerical_value*60) AS INT) END) AS min_hr_bpm, MAX(CASE '
      'WHEN mk.key="_HKPrivateWorkoutMaxHeartRate" THEN '
      'CAST(ROUND(mv.numerical_value*60) AS INT) END) AS max_hr_bpm, MAX(CASE '
      'WHEN mk.key="_HKPrivateWorkoutAverageHeartRate" THEN '
      'CAST(ROUND(mv.numerical_value*60) AS INT) END) AS avg_hr_bpm, MAX(CASE '
      'WHEN mk.key="HKWeatherTemperature" THEN ROUND(mv.numerical_value,2) '
      'END) AS temp_f, MAX(CASE WHEN mk.key="HKWeatherHumidity" THEN '
      'CAST(mv.numerical_value AS INT) END) AS humidity_pct, MAX(CASE WHEN '
      'mk.key="_HKPrivateWorkoutWeatherLocationCoordinatesLatitude" THEN '
      'mv.numerical_value END) AS lat, MAX(CASE WHEN '
      'mk.key="_HKPrivateWorkoutWeatherLocationCoordinatesLongitude" THEN '
      'mv.numerical_value END) AS lon, MAX(CASE WHEN '
      'mk.key="_HKPrivateWorkoutMinGroundElevation" THEN '
      'ROUND(mv.numerical_value,2) END) AS min_elev_m, MAX(CASE WHEN '
      'mk.key="_HKPrivateWorkoutMaxGroundElevation" THEN '
      'ROUND(mv.numerical_value,2) END) AS max_elev_m, source_devices.hardware '
      'AS hardware, sources.name AS source_name, dp.source_version AS '
      'software_version, dp.tz_name AS timezone_name, o.creation_date AS '
      'added_cocoa FROM workout_activities AS wa LEFT JOIN workouts AS w ON '
      'w.data_id = wa.owner_id LEFT JOIN workout_statistics AS ws ON '
      'ws.workout_activity_id = wa.ROWID LEFT JOIN samples AS s ON s.data_id = '
      'w.data_id LEFT JOIN metadata_values AS mv ON mv.object_id = wa.owner_id '
      'LEFT JOIN metadata_keys AS mk ON mk.ROWID = mv.key_id LEFT JOIN objects '
      'AS o ON o.data_id = wa.owner_id LEFT JOIN data_provenances AS dp ON '
      'dp.ROWID = o.provenance LEFT JOIN source_devices ON '
      'source_devices.ROWID = dp.device_id LEFT JOIN sources ON sources.ROWID '
      '= dp.source_id GROUP BY wa.ROWID ORDER BY wa.start_date'),
      'ParseWorkoutActivitiesRow')]

  SCHEMAS = {
      'workout_activities': (
          'CREATE TABLE workout_activities (ROWID INTEGER PRIMARY KEY, '
          'owner_id INTEGER, activity_type INTEGER, start_date INTEGER, '
          'end_date INTEGER, duration REAL, location_type INTEGER)'),
      'workouts': (
          'CREATE TABLE workouts (data_id INTEGER PRIMARY KEY, total_distance '
          'REAL, goal_type INTEGER, goal TEXT)'),
      'samples': (
          'CREATE TABLE samples (data_id INTEGER PRIMARY KEY, start_date '
          'INTEGER, end_date INTEGER)'),
      'workout_statistics': (
          'CREATE TABLE workout_statistics (workout_activity_id INTEGER, '
          'data_type INTEGER, quantity REAL)'),
      'source_devices': (
          'CREATE TABLE source_devices (ROWID INTEGER PRIMARY KEY, hardware '
          'TEXT)'),
      'sources': (
          'CREATE TABLE sources (ROWID INTEGER PRIMARY KEY, name TEXT)')}

  REQUIRE_SCHEMA_MATCH = False

  def _GetDateTimeRowValue(self, query_hash, row, value_name):
    """Retrieves CocoaTime from an integer timestamp column."""
    ts = self._GetRowValue(query_hash, row, value_name)
    if ts is None:
      return None
    try:
      return dfdatetime_cocoa_time.CocoaTime(timestamp=int(ts))
    except (ValueError, TypeError):
      return None

  def _CopyToRfc3339String(self, dfdt):
    """Returns RFC3339/ISO string from a dfdatetime object or None."""
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
    """Converts seconds to 'HH:MM:SS'."""
    try:
      total = int(float(seconds_value))
    except (TypeError, ValueError):
      return None
    hours = total // 3600
    minutes = (total % 3600) // 60
    seconds = total % 60
    return f'{hours:02d}:{minutes:02d}:{seconds:02d}'

  def _DistanceToKmMiles(self, km_value):
    """Converts distance to (km, miles). Assumes input in KM."""
    try:
      km = float(km_value)
    except (TypeError, ValueError):
      return None, None
    miles = km * 0.621371
    return km, miles

  def ParseWorkoutActivitiesRow(
      self, parser_mediator, query, row, **unused_kwargs):
    """Parses a row from workout_activities local join."""
    qh = hash(query)
    event_data = IOSHealthWorkoutsLatestEventData()

    event_data.start_date = self._GetDateTimeRowValue(qh, row, 'start_cocoa')
    event_data.end_date = self._GetDateTimeRowValue(qh, row, 'end_cocoa')
    event_data.start_date_str = self._CopyToRfc3339String(event_data.start_date)
    event_data.end_date_str = self._CopyToRfc3339String(event_data.end_date)
    event_data.date_time = event_data.start_date
    event_data.activity_type = self._GetRowValue(qh, row, 'activity_type_code')
    event_data.location_type = self._GetRowValue(qh, row, 'location_type_code')
    event_data.goal_type = self._GetRowValue(qh, row, 'goal_type_code')
    duration_seconds = self._GetRowValue(qh, row, 'duration_seconds')
    event_data.workout_duration = self._SecondsToHMS(duration_seconds)

    if duration_seconds is not None:
      try:
        event_data.duration_in_minutes = float(duration_seconds) / 60.0
      except (TypeError, ValueError):
        event_data.duration_in_minutes = None

    sample_start = self._GetRowValue(qh, row, 'sample_start_cocoa')
    sample_end = self._GetRowValue(qh, row, 'sample_end_cocoa')
    try:
      if sample_end is not None and sample_start is not None:
        total_secs = int(sample_end) - int(sample_start)
        event_data.total_time_duration = self._SecondsToHMS(total_secs)
    except (TypeError, ValueError):
      event_data.total_time_duration = None

    km_raw = self._GetRowValue(qh, row, 'total_distance_km')
    km, miles = self._DistanceToKmMiles(km_raw)
    event_data.total_distance_km = round(km, 2) if km is not None else None
    event_data.total_distance_miles = round(
        miles, 2) if miles is not None else None

    event_data.goal = self._GetRowValue(qh, row, 'goal_value')
    act = self._GetRowValue(qh, row, 'total_active_kcal')
    rest = self._GetRowValue(qh, row, 'total_resting_kcal')
    event_data.total_active_energy_kcal = round(
        float(act), 2) if act is not None else None
    event_data.total_resting_energy_kcal = round(
        float(rest), 2) if rest is not None else None

    event_data.average_mets = self._GetRowValue(qh, row, 'avg_mets')
    event_data.min_heart_rate_bpm = self._GetRowValue(qh, row, 'min_hr_bpm')
    event_data.max_heart_rate_bpm = self._GetRowValue(qh, row, 'max_hr_bpm')
    event_data.avg_heart_rate_bpm = self._GetRowValue(qh, row, 'avg_hr_bpm')
    temp_f = self._GetRowValue(qh, row, 'temp_f')
    event_data.temperature_f = temp_f

    if temp_f is not None:
      try:
        event_data.temperature_c = round(
            ((float(temp_f) - 32.0) * (5.0 / 9.0)), 2)
      except (TypeError, ValueError):
        event_data.temperature_c = None

    event_data.humidity_percent = self._GetRowValue(qh, row, 'humidity_pct')
    event_data.latitude = self._GetRowValue(qh, row, 'lat')
    event_data.longitude = self._GetRowValue(qh, row, 'lon')
    event_data.min_ground_elevation_m = self._GetRowValue(qh, row, 'min_elev_m')
    event_data.max_ground_elevation_m = self._GetRowValue(qh, row, 'max_elev_m')
    event_data.hardware = self._GetRowValue(qh, row, 'hardware')
    event_data.source = self._GetRowValue(qh, row, 'source_name')
    event_data.software_version = self._GetRowValue(qh, row, 'software_version')
    event_data.timezone = self._GetRowValue(qh, row, 'timezone_name')
    event_data.added_timestamp = self._GetDateTimeRowValue(
        qh, row, 'added_cocoa')
    event_data.added_timestamp_str = self._CopyToRfc3339String(
        event_data.added_timestamp)

    parser_mediator.ProduceEventData(event_data)


sqlite.SQLiteParser.RegisterPlugin(IOSHealthWorkoutsLatestPlugin)
