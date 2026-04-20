# -*- coding: utf-8 -*-
"""SQLite parser plugin for Android App Launch (SimpleStorage) database file."""

from dfdatetime import java_time as dfdatetime_java_time

from plaso.containers import events
from plaso.parsers import sqlite
from plaso.parsers.sqlite_plugins import interface

class AndroidAppLaunch(events.EventData):
  """Android App Launch event data.
    Attributes:
      date (dfdatetime.DateTimeValues): date and time the app was launch.
      package_name (str): The unique package identifier of the app.
      launch_location_id (int): Id of location where the app was launch.
      prediction_ui_surface_id (int): Id of UI surface where prediction was 
      made.
      prediction_source_id (int): Id that indicates the source of prediction.
      prediction_rank (int): A value that indicates the relevance of the 
      prediction.
      id (int): An identifier.
  """

  DATA_TYPE = 'android:sqlite:app_launch'

  def __init__(self):
    """Initializes event data."""
    super(AndroidAppLaunch, self).__init__(data_type=self.DATA_TYPE)
    self.launch_time = None
    self.package_name = None
    self.launch_location_id = None
    self.prediction_ui_surface_id = None
    self.prediction_source_id = None
    self.prediction_rank = None
    self.id = None

class AndroidAppLaunchPlugin(interface.SQLitePlugin):
  """
    SQLite parser plugin for Android App Launch (SimpleStorage) database files.
  """

  NAME = 'android_app_launch'
  DATA_FORMAT = 'Android App Launch SQLite database (SimpleStorage) file'

  REQUIRED_STRUCTURE = {
    'EchoAppLaunchMetricsEvents': frozenset([
      'timestampMillis', 'packageName', 'launchLocationId', 
      'predictionUiSurfaceId', 'predictionSourceId', 'predictionRank', 'id'])
  }

  QUERIES = [((
    'SELECT timestampMillis, packageName, launchLocationId, '
    'predictionUiSurfaceId, predictionSourceId, predictionRank, id '
    'FROM EchoAppLaunchMetricsEvents'),
    'ParseAppLaunchRow'
  )]

  SCHEMAS = {
    'EchoAppLaunchMetricsEvents': (
      'CREATE TABLE `EchoAppLaunchMetricsEvents` '
      '(`timestampMillis` INTEGER NOT NULL, `packageName` TEXT NOT NULL, '
      '`launchLocationId` INTEGER NOT NULL, `predictionUiSurfaceId` '
      'INTEGER NOT NULL, `predictionSourceId` INTEGER NOT NULL, '
      '`predictionRank` INTEGER NOT NULL, `id` INTEGER PRIMARY '
      'KEY AUTOINCREMENT NOT NULL, FOREIGN KEY(`packageName`) REFERENCES '
      '`Packages`(`packageName`) ON UPDATE CASCADE ON DELETE CASCADE )'
    ),
    'Packages': (
      'CREATE TABLE `Packages` (`packageName` TEXT NOT NULL, '
      '`loggablePackageName` TEXT NOT NULL, PRIMARY KEY(`packageName`))'
    )
  }

  def _GetTimeRowValue(self, query_hash, row, value_name):
    """Retrieves a date and time value from the row.
    Args:
      query_hash (int): hash of the query, that uniquely identifies the query
      that produced the row.
      row (sqlite3.Row): row.
      Returns:
    dfdatetime.JavaTime: date and time value or None if not available.
    """
    timestamp = self._GetRowValue(query_hash, row, value_name)
    if timestamp is None:
      return None

    return dfdatetime_java_time.JavaTime(timestamp=timestamp)

  # pylint: disable=unused-argument
  def ParseAppLaunchRow(
    self, parser_mediator, query, row, **unused_kwargs):
    """Parses an account row.
    
    Args:
      parser_mediator (ParserMediator): mediates interactions between parsers
      and other components, such as storage and dfVFS.
      query (str): query that created the row.
      row (sqlite3.Row): row.
    """
    query_hash = hash(query)

    event_data = AndroidAppLaunch()
    event_data.launch_time = self._GetTimeRowValue(query_hash, row,
      'timestampMillis')
    event_data.package_name = self._GetRowValue(query_hash, row, 'packageName')
    event_data.launch_location_id = self._GetRowValue(query_hash, row,
      'launchLocationId')
    event_data.prediction_ui_surface_id = self._GetRowValue(query_hash, row,
      'predictionUiSurfaceId')
    event_data.prediction_source_id = self._GetRowValue(query_hash, row,
      'predictionSourceId')
    event_data.prediction_rank = self._GetRowValue(query_hash, row,
      'predictionRank')
    event_data.id = self._GetRowValue(query_hash, row, 'id')


    parser_mediator.ProduceEventData(event_data)

sqlite.SQLiteParser.RegisterPlugin(AndroidAppLaunchPlugin)
