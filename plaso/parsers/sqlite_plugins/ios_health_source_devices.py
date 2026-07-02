"""SQLite parser plugin for iOS Health Source Devices iOS 15 data."""

from dfdatetime import cocoa_time as dfdatetime_cocoa_time

from plaso.containers import events
from plaso.parsers import sqlite
from plaso.parsers.sqlite_plugins import interface


class IOSHealthSourceDevicesEventData(events.EventData):
    """iOS Health Source Devices event data.

    Attributes:
      added_time (dfdatetime.DateTimeValues): date and time the device was added to the
          database.
      device_name (str): name of the device.
      firmware (str): firmware version of the device.
      hardware (str): hardware version of the device.
      local_identifier (str): local identifier.
      manufacturer (str): manufacturer of the device.
      model (str): model of the device.
      software (str): software version of the device.
      sync_provenance (int): sync provenance information.
    """

    DATA_TYPE = "ios:health:source_devices"

    def __init__(self):
        """Initializes event data."""
        super().__init__(data_type=self.DATA_TYPE)
        self.added_time = None
        self.device_name = None
        self.firmware = None
        self.hardware = None
        self.local_identifier = None
        self.manufacturer = None
        self.model = None
        self.software = None
        self.sync_provenance = None


class IOSHealthSourceDevicesPlugin(interface.SQLitePlugin):
    """SQLite parser plugin for iOS Health Source Devices data."""

    NAME = "ios_health_source_devices"
    DATA_FORMAT = "iOS Health Source Devices Data from healthdb.sqlite"

    REQUIRED_STRUCTURE = {
        "source_devices": frozenset(
            [
                "creation_date",
                "firmware",
                "hardware",
                "localIdentifier",
                "manufacturer",
                "model",
                "name",
                "software",
                "sync_provenance",
            ]
        )
    }

    QUERIES = [
        (
            (
                "SELECT creation_date, firmware, hardware, localIdentifier, "
                "manufacturer, model, name, software, sync_provenance "
                "FROM source_devices WHERE name NOT LIKE '__NONE__' AND "
                "localIdentifier NOT LIKE '__NONE__'"
            ),
            "ParseSourceDevicesRow",
        )
    ]

    SCHEMAS = {
        "source_devices": (
            "CREATE TABLE source_devices (data_id INTEGER PRIMARY KEY, name "
            "TEXT, manufacturer TEXT, model TEXT, hardware TEXT, firmware TEXT, "
            "software TEXT, localIdentifier TEXT, sync_provenance TEXT, "
            "creation_date INTEGER)"
        )
    }

    REQUIRE_SCHEMA_MATCH = False

    def _GetDateTimeRowValue(self, query_hash, row, value_name):
        """Retrieves a Cocoa DateTime value from a row.

        Args:
          query_hash (int): hash of the query.
          row (sqlite3.Row): row.
          value_name (str): name of the value.

        Returns:
          dfdatetime.CocoaTime: Date and time value or None.
        """
        timestamp = self._GetRowValue(query_hash, row, value_name)
        if timestamp is None:
            return None

        try:
            ts_float = float(timestamp)
            if ts_float == 0:
                return None
            return dfdatetime_cocoa_time.CocoaTime(timestamp=ts_float)
        except (ValueError, TypeError):
            return None

    def ParseSourceDevicesRow(self, parser_mediator, query, row, **unused_kwargs):
        """Parses a single source device row.

        Args:
          parser_mediator (ParserMediator): mediates interactions.
          query (str): query that created the row.
          row (sqlite3.Row): row.
        """
        query_hash = hash(query)

        local_identifier = self._GetRowValue(query_hash, row, "localIdentifier")

        event_data = IOSHealthSourceDevicesEventData()
        event_data.added_time = self._GetDateTimeRowValue(
            query_hash, row, "creation_date"
        )
        event_data.device_name = self._GetRowValue(query_hash, row, "name")
        event_data.firmware = self._GetRowValue(query_hash, row, "firmware") or None
        event_data.hardware = self._GetRowValue(query_hash, row, "hardware")
        event_data.local_identifier = local_identifier or None
        event_data.manufacturer = self._GetRowValue(query_hash, row, "manufacturer")
        event_data.model = self._GetRowValue(query_hash, row, "model")
        event_data.software = self._GetRowValue(query_hash, row, "software")
        event_data.sync_provenance = self._GetRowValue(
            query_hash, row, "sync_provenance"
        )
        parser_mediator.ProduceEventData(event_data)


sqlite.SQLiteParser.RegisterPlugin(IOSHealthSourceDevicesPlugin)
