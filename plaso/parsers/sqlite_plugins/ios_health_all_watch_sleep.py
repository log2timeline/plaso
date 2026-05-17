"""SQLite parser plugin for iOS Health - All Watch Sleep Data."""

from dfdatetime import cocoa_time as dfdatetime_cocoa_time

from plaso.containers import events
from plaso.parsers import sqlite
from plaso.parsers.sqlite_plugins import interface


class IOSHealthAllWatchSleepEventData(events.EventData):
    """iOS Health - All Watch Sleep event data (raw code: 0/1).

    Attributes:
      end_time (dfdatetime.DateTimeValues): date and time the sleep ended.
      sleep_state_code (int): sleep state code (0 or 1).
      sleep_state_hms (str): duration of sleep formatted as 'HH:MM:SS'.
      start_time (dfdatetime.DateTimeValues): date and time the sleep started.
    """

    DATA_TYPE = "ios:health:all_watch_sleep"

    def __init__(self):
        """Initializes event data."""
        super().__init__(data_type=self.DATA_TYPE)
        self.end_time = None
        self.sleep_state_code = None
        self.sleep_state_hms = None
        self.start_time = None


class IOSHealthAllWatchSleepPlugin(interface.SQLitePlugin):
    """SQLite parser plugin for iOS Health - All Watch Sleep Data (iOS 13–16)."""

    NAME = "ios_health_all_watch_sleep_data"
    DATA_FORMAT = (
        "iOS Health Sleep (Apple Watch) from healthdb_secure.sqlite (iOS 13–16)"
    )

    REQUIRED_STRUCTURE = {
        "samples": frozenset(["data_id", "start_date", "end_date", "data_type"]),
        "category_samples": frozenset(["data_id", "value"]),
        "objects": frozenset(["data_id", "provenance"]),
        "data_provenances": frozenset(["origin_product_type"]),
    }

    QUERIES = [
        (
            (
                "SELECT "
                "s.start_date AS start_date, "
                "s.end_date AS end_date, "
                "cs.value AS category_value "
                "FROM samples s "
                "LEFT JOIN category_samples cs ON s.data_id = cs.data_id "
                "LEFT JOIN objects o ON s.data_id = o.data_id "
                "LEFT JOIN data_provenances dp ON o.provenance = dp.rowid "
                'AND dp.origin_product_type LIKE "%Watch%" '
                'WHERE s.data_type IN (63, "63") AND cs.value IN (0, 1) '
                "ORDER BY s.start_date ASC"
            ),
            "ParseSleepRow",
        )
    ]

    def _GetCocoaDateTime(self, query_hash, row, value_name):
        """Retrieves a Cocoa Time value from the row.

        Args:
          query_hash (int): hash of the query.
          row (sqlite3.Row): row.
          value_name (str): name of the value.

        Returns:
          dfdatetime.CocoaTime: Date and time value or None.
        """
        ts = self._GetRowValue(query_hash, row, value_name)
        if ts is None:
            return None
        return dfdatetime_cocoa_time.CocoaTime(timestamp=ts)

    @staticmethod
    def _SecondsToHMS(seconds_value):
        """Converts seconds to HH:MM:SS format.

        Args:
          seconds_value (int|float): total seconds.

        Returns:
          str: formatted string or None.
        """
        try:
            total = int(float(seconds_value))
        except (TypeError, ValueError):
            return None
        hh = total // 3600
        mm = (total % 3600) // 60
        ss = total % 60
        return f"{hh:02d}:{mm:02d}:{ss:02d}"

    def ParseSleepRow(self, parser_mediator, query, row, **unused_kwargs):
        """Parses a sleep sample.

        Args:
          parser_mediator (ParserMediator): mediates interactions between
              parsers and other components, such as storage and dfVFS.
          query (str): query that created the row.
          row (sqlite3.Row): row.
        """
        query_hash = hash(query)

        event_data = IOSHealthAllWatchSleepEventData()

        event_data.start_time = self._GetCocoaDateTime(query_hash, row, "start_date")
        event_data.end_time = self._GetCocoaDateTime(query_hash, row, "end_date")
        event_data.sleep_state_code = self._GetRowValue(
            query_hash, row, "category_value"
        )

        duration_seconds = None
        if (
            event_data.start_time
            and event_data.end_time
            and event_data.end_time.timestamp is not None
            and event_data.start_time.timestamp is not None
        ):
            duration_seconds = (
                event_data.end_time.timestamp - event_data.start_time.timestamp
            )

        event_data.sleep_state_hms = self._SecondsToHMS(duration_seconds)

        parser_mediator.ProduceEventData(event_data)


sqlite.SQLiteParser.RegisterPlugin(IOSHealthAllWatchSleepPlugin)
