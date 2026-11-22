# How to write a SQLite plugin

## Locate/create test data

* Before writing the plugin you'll need to have a SQLite database file to test
  the plugin with. Either generate one, or have one that does not contain
  personal data (since it will get checked into the project).
* Start by listing out all the SQL commands you'll need to issue against the
  database beforehand. Try them out manually, see if they work and produce the
  data you are looking for.

## Create file and class

* Plugin file in `plaso/parsers/sqlite_plugins/`
  * Create a subclass of [EventData](../api/plaso.containers.html#plaso.containers.events.EventData)
    for the event data the plugin extracts
  * Create a subclass of [SQLitePlugin](../api/plaso.parsers.sqlite_plugins.html#plaso.parsers.sqlite_plugins.interface.SQLitePlugin)
  * Register it with the SQLite parser by calling
    [SQLiteParser.RegisterPlugin](../api/plaso.parsers.html#plaso.parsers.interface.BaseParser.RegisterPlugin)
* Test file in `tests/parsers/sqlite_plugins/`
  * Create a subclass of `tests.parsers.sqlite_plugins.test_lib.SQLitePluginTestCase`
* Test data in `test_data/`

## Write minimal tests

* Write a test that loads your plugin and parses a file.
* It will fail initially, but running the test while you're developing your
  plugin gives you a quick way to see if your code is doing what you expect.

`SQLitePluginTestCase._ParseDatabaseFileWithPlugin()` parses a database file in
the test data directory with a specific plugin and returns a storage writer
that contains the extracted event data, for example:

```python
    def testProcess(self):
        """Tests the Process function."""
        plugin = android_app_usage.AndroidSQLiteAppUsage()
        storage_writer = self._ParseDatabaseFileWithPlugin(
            ["android", "app_usage"], plugin
        )

        number_of_event_data = storage_writer.GetNumberOfAttributeContainers(
            "event_data"
        )
        self.assertEqual(number_of_event_data, 11545)

        expected_event_values = {
            "data_type": "android:sqlite:app_usage",
            "package_name": "com.whatsapp",
            "start_time": "2023-05-31T01:29:31.577+00:00",
        }

        event_data = storage_writer.GetAttributeContainerByIndex("event_data", 339)
        self.CheckEventData(event_data, expected_event_values)
```

## Develop plugin

* Implement your subclass of [SQLitePlugin](../api/plaso.parsers.sqlite_plugins.html#plaso.parsers.sqlite_plugins.interface.SQLitePlugin)
* You'll need to define/override:
  * NAME, a short and unique name of the plugin
  * DATA_FORMAT, a description of the data format the plugin supports
  * REQUIRED_STRUCTURE, the tables and columns that must be present in the
    database for the plugin to run. Only include the tables and columns the
    queries of the plugin use, or that are needed to distinguish the database
    from similar databases.
  * QUERIES, a list of tuples of a SQL query and the name of the callback
    method that is called for every row the query returns
  * SCHEMAS, the database schemas the plugin was developed for
  * a callback method for every query, with the signature
    `(self, parser_mediator, query, row, **unused_kwargs)`, that passes the
    event data it extracts to `parser_mediator.ProduceEventData(event_data)`

The `SQLitePlugin` class provides helper methods to read row values, such as
`_GetRowValue()` and `_GetPosixTimeInMillisecondsRowValue()`. For example:

```python
"""SQLite parser plugin for Android application usage database files."""

from plaso.containers import events
from plaso.parsers import sqlite
from plaso.parsers.sqlite_plugins import interface


class AndroidAppUsage(events.EventData):
    """Android application usage event data.

    Attributes:
      package_name (str): name of the launched package.
      start_time (dfdatetime.DateTimeValues): date and time when the application
          was launched.
    """

    DATA_TYPE = "android:sqlite:app_usage"

    def __init__(self):
        """Initializes event data."""
        super().__init__(data_type=self.DATA_TYPE)
        self.package_name = None
        self.start_time = None


class AndroidSQLiteAppUsage(interface.SQLitePlugin):
    """SQLite parser plugin for Android application usage database files."""

    NAME = "android_app_usage"
    DATA_FORMAT = "Android application usage SQLite database (app_usage) file"

    REQUIRED_STRUCTURE = {
        "events": frozenset(["_id", "package_id", "timestamp"]),
        "packages": frozenset(["_id", "package_name"]),
    }

    QUERIES = [
        (
            (
                "SELECT events.timestamp, packages.package_name FROM events "
                "JOIN packages ON packages._id = events.package_id"
            ),
            "_ParseAppUsageRow",
        )
    ]

    SCHEMAS = [
        {
            "events": (
                'CREATE TABLE "events" (_id INTEGER PRIMARY KEY,timestamp INTEGER '
                "NOT NULL,type INTEGER NOT NULL,package_id INTEGER NOT NULL "
                "REFERENCES packages(_id) ON UPDATE CASCADE ON DELETE CASCADE, "
                "instance_id INTEGER DEFAULT NULL, task_root_package_id INTEGER "
                "DEFAULT NULL REFERENCES packages(_id) ON UPDATE CASCADE ON DELETE "
                "CASCADE)"
            ),
            "packages": (
                "CREATE TABLE packages (_id INTEGER PRIMARY KEY,package_name TEXT, "
                "UNIQUE(package_name) ON CONFLICT ABORT)"
            ),
        }
    ]

    def _ParseAppUsageRow(self, parser_mediator, query, row, **unused_kwargs):
        """Parses an event record row.

        Args:
          parser_mediator (ParserMediator): mediates interactions between parsers
              and other components, such as storage and dfVFS.
          query (str): query that created the row.
          row (sqlite3.Row): row.
        """
        query_hash = hash(query)

        event_data = AndroidAppUsage()
        event_data.package_name = self._GetRowValue(query_hash, row, "package_name")
        event_data.start_time = self._GetPosixTimeInMillisecondsRowValue(
            query_hash, row, "timestamp"
        )

        parser_mediator.ProduceEventData(event_data)


sqlite.SQLiteParser.RegisterPlugin(AndroidSQLiteAppUsage)
```

This is the plugin in `plaso/parsers/sqlite_plugins/android_app_usage.py`. The
class attributes and helper methods are defined in
`plaso/parsers/sqlite_plugins/interface.py`.

## Expand tests

* Add additional tests that test your plugin

## Register classes

* Edit `plaso/parsers/sqlite_plugins/__init__.py` to import your plugin in the
  correct alphabetical order.

## Extend the timeliner and formatters configurations

Extend the timeliner configuration `plaso/data/timeliner.yaml` and the
formatters configuration `plaso/data/formatters/*.yaml` with the necessary
definitions for new event data types.

See: [How to write a parser or (parser) plugin](How-to-write-a-parser.md)

## Code review/submit

* Create a PR to have the changes reviewed and merged with the main branch.
