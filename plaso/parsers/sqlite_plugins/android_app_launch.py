"""SQLite parser plugin for Android application launch database files."""

from plaso.containers import events
from plaso.parsers import sqlite
from plaso.parsers.sqlite_plugins import interface


class AndroidAppLaunch(events.EventData):
    """Android application launch event data.

    Attributes:
      identifier (int): identifier.
      launch_location_identifier (int): identifier of the location where the app
          was launched.
      package_name (str): name of the package of the app.
      prediction_rank (int): relevance of the prediction.
      prediction_source_identifier (int): identifier of the source of prediction.
      prediction_ui_surface_identifier (int): identifier of the UI surface where
          prediction was made.
      start_time (dfdatetime.DateTimeValues): date and time the application was
          started (or launched).
    """

    DATA_TYPE = "android:sqlite:app_launch"

    def __init__(self):
        """Initializes event data."""
        super().__init__(data_type=self.DATA_TYPE)
        self.identifier = None
        self.launch_location_identifier = None
        self.package_name = None
        self.prediction_rank = None
        self.prediction_source_identifier = None
        self.prediction_ui_surface_identifier = None
        self.start_time = None


class AndroidAppLaunchPlugin(interface.SQLitePlugin):
    """SQLite parser plugin for Android application launch database files."""

    NAME = "android_app_launch"
    DATA_FORMAT = "Android application launch SQLite database (SimpleStorage) file"

    REQUIRED_STRUCTURE = {
        "EchoAppLaunchMetricsEvents": frozenset(
            [
                "id",
                "launchLocationId",
                "packageName",
                "predictionRank",
                "predictionSourceId",
                "predictionUiSurfaceId",
                "timestampMillis",
            ]
        )
    }

    QUERIES = [
        (
            (
                "SELECT id, launchLocationId, packageName, predictionRank, "
                "predictionSourceId, predictionUiSurfaceId, timestampMillis "
                "FROM EchoAppLaunchMetricsEvents"
            ),
            "_ParseAppLaunchRow",
        )
    ]

    SCHEMAS = {
        "EchoAppLaunchMetricsEvents": (
            "CREATE TABLE `EchoAppLaunchMetricsEvents` "
            "(`timestampMillis` INTEGER NOT NULL, `packageName` TEXT NOT NULL, "
            "`launchLocationId` INTEGER NOT NULL, `predictionUiSurfaceId` "
            "INTEGER NOT NULL, `predictionSourceId` INTEGER NOT NULL, "
            "`predictionRank` INTEGER NOT NULL, `id` INTEGER PRIMARY "
            "KEY AUTOINCREMENT NOT NULL, FOREIGN KEY(`packageName`) REFERENCES "
            "`Packages`(`packageName`) ON UPDATE CASCADE ON DELETE CASCADE )"
        ),
        "Packages": (
            "CREATE TABLE `Packages` (`packageName` TEXT NOT NULL, "
            "`loggablePackageName` TEXT NOT NULL, PRIMARY KEY(`packageName`))"
        ),
    }

    def _ParseAppLaunchRow(self, parser_mediator, query, row, **unused_kwargs):
        """Parses an event record row.

        Args:
          parser_mediator (ParserMediator): mediates interactions between parsers
              and other components, such as storage and dfVFS.
          query (str): query that created the row.
          row (sqlite3.Row): row.
        """
        query_hash = hash(query)

        event_data = AndroidAppLaunch()
        event_data.identifier = self._GetRowValue(query_hash, row, "id")
        event_data.launch_location_identifier = self._GetRowValue(
            query_hash, row, "launchLocationId"
        )
        event_data.package_name = self._GetRowValue(query_hash, row, "packageName")
        event_data.prediction_rank = self._GetRowValue(
            query_hash, row, "predictionRank"
        )
        event_data.prediction_source_identifier = self._GetRowValue(
            query_hash, row, "predictionSourceId"
        )
        event_data.prediction_ui_surface_identifier = self._GetRowValue(
            query_hash, row, "predictionUiSurfaceId"
        )
        event_data.start_time = self._GetJavaTimeRowValue(
            query_hash, row, "timestampMillis"
        )
        parser_mediator.ProduceEventData(event_data)


sqlite.SQLiteParser.RegisterPlugin(AndroidAppLaunchPlugin)
