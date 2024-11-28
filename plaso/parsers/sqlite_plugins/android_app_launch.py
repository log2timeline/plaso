# -*- coding: utf-8 -*-
"""SQLite parser plugin for Android App Launch (SimpleStorage) database files."""

from dfdatetime import posix_time as dfdatetime_posix_time

from plaso.containers import events
from plaso.parsers import sqlite
from plaso.parsers.sqlite_plugins import interface

class AndroidAppLaunch(events.EventData):
 """Android App Launch event data.
    Attributes:
        date (dfdatetime.DateTimeValues): date and time the app was launch.
        package_name (str): The unique package identifier of the app.
        launch_location_id (int): id of location where the app was launch.
        id (int): identifier
    """

    DATA_TYPE = 'android:sqlite:app_launch'

    def __init__(self):
        """Initializes event data."""
        super(AndroidAppLaunch, self).__init__(data_type=self.DATA_TYPE)
        self.date = None
        self.package_name = None
        self.launch_location_id = None
        self.id = None

class AndroidAppLaunchPlugin(interface.SQLitePlugin):
    """SQLite parser plugin for Android App Launch (SimpleStorage) database files."""

    NAME = 'android_app_launch'
    DATA_FORMAT = 'Android App Launch SQLite database (SimpleStorage) file'

    REQUIRED_STRUCTURE = {
        'EchoAppLaunchMetricsEvents': frozenset([
            'timestampMillis', 'packageName', 'launchLoactionId', 'id'])
    }

    QUERIES = [((
        'SELECT EchoAppLaunchMetricsEvents.timestampMillis, EchoAppLaunchMetricsEvents.packageName, '
        'EchoAppLaunchMetricsEvents.launchLoactionId, EchoAppLaunchMetricsEvents.id '
        'FROM EchoAppLaunchMetricsEvents'),
        'ParseAppLaunchRow')]
    
    SCHEMAS = {
        'EchoAppLaunchMetricsEvents': (
            'CREATE TABLE EchoAppLaunchMetricsEvents (timestampMillis INTEGER, packageName TEXT, '
            'launchLocationId INTEGER, predictionUiSurfaceId INTEGER, predictionSourceId INTEGER, '
            'predictionRank INTEGER, id INTEGER PRIMARY KEY ')
    }
    
    REQUIRES_SCHEMA_MATCH = False

    def _GetTimeRowValue(self, query_hash, row, value_name):
        """Retrieves a date and time value from the row.
        Args:
            query_hash (int): hash of the query, that uniquely identifies the query that produced the row.
            row (sqlite3.Row): row.
            value_name (str): name of the value.
        Returns:
            dfdatetime.Posixtime: date and time value or None if not available.
        """
        timestamp = self._GetRowValue(query_hash, row, value_name)
        if timestamp is None:
            return None

        return dfdatetime_posix_time.PosixTimeInMilliseconds(timestamp=timestamp)

        # pylint: disable=unused-argument
    def ParseAppLaunchRow(
        self, parser_mediator, query, row, **unused_kwargs):
        """Parses an account row.
        
        Args:
            parser_mediator (ParserMediator): mediates interactions between parsers and other components, such as storage and dfVFS.
            query (str): query that created the row.
            row (sqlite3.Row): row.
        """
        query_hash = hash(query)    

        event_data = AndroidAppLaunch()
        event_data.date = self._GetTimeRowValue(query_hash, row, 'timestampMillis')
        event_data.package_name = self._GetRowValue(query_hash, row, 'packageName')
        event_data.launch_location_id = self._GetRowValue(query_hash, row, 'launchLocationId')
        event_data.id = self._GetRowValue(query_hash, row, 'id')


        parser_mediator.ProduceEventData(event_data)

sqlite.SQLiteParser.RegisterPlugin(AndroidAppLaunchPlugin)