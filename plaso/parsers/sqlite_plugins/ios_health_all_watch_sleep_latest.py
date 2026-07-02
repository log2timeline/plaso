"""SQLite parser plugin for iOS Health - All Watch Sleep Data (iOS 17)."""

from dfdatetime import cocoa_time as dfdatetime_cocoa_time

from plaso.containers import events
from plaso.parsers import sqlite
from plaso.parsers.sqlite_plugins import interface


class IOSHealthAllWatchSleepLatestEventData(events.EventData):
    """iOS Health - All Watch Sleep (stages) event data.

    Attributes:
      end_time (dfdatetime.DateTimeValues): date and time the sleep ended.
      sleep_state_code (int): sleep state code (stages 2-5).
      sleep_state_hms (str): duration of sleep formatted as 'HH:MM:SS'.
      start_time (dfdatetime.DateTimeValues): date and time the sleep started.
    """

    DATA_TYPE = "ios:health:all_watch_sleep_ios17"

    def __init__(self):
        """Initializes event data."""
        super().__init__(data_type=self.DATA_TYPE)
        self.end_time = None
        self.sleep_state_code = None
        self.sleep_state_hms = None
        self.start_time = None


class IOSHealthAllWatchSleepLatestPlugin(interface.SQLitePlugin):
    """SQLite parser plugin for iOS Health Sleep Stages (iOS 17+)."""

    NAME = "ios_health_all_watch_sleep_ios17"
    DATA_FORMAT = "iOS Health Sleep Stages from healthdb_secure.sqlite (iOS 17+)"

    REQUIRED_STRUCTURE = {
        "samples": frozenset(["data_id", "start_date", "end_date"]),
        "category_samples": frozenset(["data_id", "value"]),
    }

    QUERIES = [
        (
            (
                "SELECT s.start_date AS start_date, "
                "s.end_date AS end_date, "
                "cs.value AS category_value "
                "FROM samples s "
                "JOIN category_samples cs ON s.data_id = cs.data_id"
            ),
            "ParseSleepRow",
        )
    ]

    def _GetCocoaDateTime(self, qh, row, name):
        """Retrieves a Cocoa Time value from the row.

        Args:
          qh (int): hash of the query.
          row (sqlite3.Row): row.
          name (str): name of the value.

        Returns:
          dfdatetime.CocoaTime: Date and time value or None.
        """
        ts = self._GetRowValue(qh, row, name)
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
        """Parses a sleep data row.

        Args:
          parser_mediator (ParserMediator): mediates interactions.
          query (str): query that created the row.
          row (sqlite3.Row): row.
        """
        query_hash = hash(query)

        raw_code = self._GetRowValue(query_hash, row, "category_value")
        try:
            code = int(raw_code) if raw_code is not None else None
        except (TypeError, ValueError):
            code = None

        if code not in (2, 3, 4, 5):
            return

        event_data = IOSHealthAllWatchSleepLatestEventData()

        event_data.start_time = self._GetCocoaDateTime(query_hash, row, "start_date")
        event_data.end_time = self._GetCocoaDateTime(query_hash, row, "end_date")
        event_data.sleep_state_code = code

        duration = None
        if (
            event_data.start_time
            and event_data.end_time
            and event_data.start_time.timestamp is not None
            and event_data.end_time.timestamp is not None
        ):
            duration = event_data.end_time.timestamp - event_data.start_time.timestamp

        event_data.sleep_state_hms = self._SecondsToHMS(duration)

        parser_mediator.ProduceEventData(event_data)


sqlite.SQLiteParser.RegisterPlugin(IOSHealthAllWatchSleepLatestPlugin)
