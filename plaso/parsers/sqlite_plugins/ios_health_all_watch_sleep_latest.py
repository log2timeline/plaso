"""SQLite parser plugin for iOS Health - All Watch Sleep Data (iOS 17)."""

from plaso.containers import events
from plaso.parsers import sqlite
from plaso.parsers.sqlite_plugins import interface


class IOSHealthAllWatchSleepLatestEventData(events.EventData):
    """iOS Health - All Watch Sleep (stages) event data.

    Attributes:
      duration (float): duration in seconds.
      end_time (dfdatetime.DateTimeValues): date and time the sleep ended.
      sleep_state_code (int): sleep state code (stages 2-5).
      start_time (dfdatetime.DateTimeValues): date and time the sleep started.
    """

    DATA_TYPE = "ios:health:all_watch_sleep_ios17"

    def __init__(self):
        """Initializes event data."""
        super().__init__(data_type=self.DATA_TYPE)
        self.duration = None
        self.end_time = None
        self.sleep_state_code = None
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
                "SELECT samples.start_date AS start_date, "
                "samples.end_date AS end_date, "
                "category_samples.value AS category_value "
                "FROM samples "
                "JOIN category_samples ON samples.data_id = category_samples.data_id"
            ),
            "ParseSleepRow",
        )
    ]

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

        # TODO: what do these category values represent?
        if code not in (2, 3, 4, 5):
            return

        event_data = IOSHealthAllWatchSleepLatestEventData()
        event_data.end_time = self._GetCocoaTimeRowValue(query_hash, row, "end_date")
        event_data.sleep_state_code = code
        event_data.start_time = self._GetCocoaTimeRowValue(
            query_hash, row, "start_date"
        )

        if (
            event_data.end_time
            and event_data.start_time
            and event_data.end_time.timestamp is not None
            and event_data.start_time.timestamp is not None
        ):
            event_data.duration = (
                event_data.end_time.timestamp - event_data.start_time.timestamp
            )

        parser_mediator.ProduceEventData(event_data)


sqlite.SQLiteParser.RegisterPlugin(IOSHealthAllWatchSleepLatestPlugin)
