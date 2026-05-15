"""SQLite parser plugin for Android Burner database files."""

from dfdatetime import java_time as dfdatetime_java_time

from plaso.containers import events
from plaso.parsers import sqlite
from plaso.parsers.sqlite_plugins import interface


class AndroidBurnerEventData(events.EventData):
    """Android Burner event data.

    Attributes:
      alias (str): Alias or nickname.
      creation_time (dfdatetime.DateTimeValues): Creation date and time.
      expiration_time (dfdatetime.DateTimeValues): Expiration date and time.
      last_updated_time (dfdatetime.DateTimeValues): Last update date and time.
      name (str): Name of the burner.
      phone_number (str): Associated phone number.
      total_minutes (int): Total minutes available for calls.
      user_identifier (str): User identifier.
      voicemail_url (str): URL for accessing the voicemail associated with the
          burner.
    """

    DATA_TYPE = "android:burners"

    def __init__(self):
        """Initializes event data."""
        super().__init__(data_type=self.DATA_TYPE)
        self.alias = None
        self.creation_time = None
        self.expiration_time = None
        self.last_updated_time = None
        self.name = None
        self.phone_number = None
        self.total_minutes = None
        self.user_identifier = None
        self.voicemail_url = None


class AndroidBurnerPlugin(interface.SQLitePlugin):
    """SQLite parser plugin for Android communication information database files.

    The Android communication information database file is typically stored in:
    burners.db
    """

    NAME = "android_communication_information"
    DATA_FORMAT = "Android communication information SQLite database file"

    REQUIRED_STRUCTURE = {
        "burners": frozenset(
            [
                "_id",
                "phone_number_id",
                "voicemail_url",
                "user_id",
                "name",
                "alias",
                "features",
                "total_minutes",
                "expiration_date",
                "date_created",
                "last_updated_date",
                "renewal_date",
            ]
        )
    }

    QUERIES = [
        (
            (
                "SELECT _id AS id, phone_number_id, voicemail_url, user_id, name, "
                "alias, features, total_minutes, expiration_date, date_created, "
                "last_updated_date, renewal_date FROM burners"
            ),
            "_ParseBurnersRow",
        )
    ]

    SCHEMAS = [
        {
            "android_metadata": ("CREATE TABLE android_metadata (locale TEXT)"),
            "burners": (
                "CREATE TABLE burners(_id integer primary key autoincrement, "
                "burner_id text not null unique, phone_number_id text not null, "
                "voicemail_url text, user_id text not null, name text, alias text, "
                "features text not null, total_minutes integer not null, "
                "remaining_minutes integer not null, total_texts integer not null, "
                "remaining_texts integer not null, expiration_date integer not "
                "null, ringer integer default 1, notifications integer default 1, "
                "disabled integer default 0, date_created integer not null, "
                "last_updated_date integer, extension_count integer default 0, "
                "renewal_date integer default 0, auto_reply_active integer default "
                "0, auto_reply_text text, caller_id_enabled integer default 0, "
                "useSip integer default 0, hexColor integer, call_forward_status "
                "text)"
            ),
            "connections": (
                "CREATE TABLE connections(_id integer primary key autoincrement, "
                "user_id integer not null, burner_id integer not null, name text, "
                "handle text, image_url text, service_name text not null, status "
                "text)"
            ),
            "contacts": (
                "CREATE TABLE contacts(_id integer primary key autoincrement, "
                "contact_id text not null unique, name text not null, phone_number "
                "text not null, burner_id text, date_created integer not null, "
                "last_updated_date integer not null, blocked integer default 0, "
                "muted integer default 0, notes text, images text)"
            ),
            "messages": (
                "CREATE TABLE messages(_id integer primary key autoincrement, "
                "message_id text not null unique, state integer default 0, message "
                "text not null, contact_phone_number text not null, connected "
                "integer default 0, message_type integer not null, "
                "contact_burner_id text, voice_url text, date_created integer not "
                "null, last_updated_date integer not null, read integer default 0, "
                "user_id text not null, sid text, burner_id text not null, duration "
                "integer, direction integer not null, asset_url text, send_status "
                "integer default 0 )"
            ),
            "subscriptions": (
                "CREATE TABLE subscriptions(_id integer primary key autoincrement, "
                "subscription_id text not null unique, sku text not null, receipt "
                "text not null, burner_ids text, renewal_date integer, "
                "burner_assigned_in_period integer, store text not null,canceled "
                "integer not null, cancellation_date integer)"
            ),
        }
    ]

    def _GetDateTimeRowValue(self, query_hash, row, value_name):
        """Retrieves a date and time value from the row.

        Args:
          query_hash (int): hash of the query, that uniquely identifies the query
              that produced the row.
          row (sqlite3.Row): row.
          value_name (str): name of the value.

        Returns:
          dfdatetime.JavaTime: date and time value or None if not available.
        """
        timestamp = self._GetRowValue(query_hash, row, value_name)
        if timestamp is None:
            return None

        return dfdatetime_java_time.JavaTime(timestamp=timestamp)

    def _ParseBurnersRow(self, parser_mediator, query, row, **unused_kwargs):
        """Parses a burners record row.

        Args:
        parser_mediator (ParserMediator): mediates interactions between parsers
            and other components, such as storage and dfVFS.
        query (str): query that created the row.
        row (sqlite3.Row): row.
        """
        query_hash = hash(query)

        # TODO: parse features.
        # TODO: parse renewal_date.

        event_data = AndroidBurnerEventData()
        event_data.alias = self._GetRowValue(query_hash, row, "alias")
        event_data.creation_time = self._GetDateTimeRowValue(
            query_hash, row, "date_created"
        )
        event_data.expiration_time = self._GetDateTimeRowValue(
            query_hash, row, "expiration_date"
        )
        event_data.last_updated_time = self._GetDateTimeRowValue(
            query_hash, row, "last_updated_date"
        )
        event_data.name = self._GetRowValue(query_hash, row, "name")
        event_data.phone_number = self._GetRowValue(query_hash, row, "phone_number_id")
        event_data.total_minutes = self._GetRowValue(query_hash, row, "total_minutes")
        event_data.user_identifier = self._GetRowValue(query_hash, row, "user_id")
        event_data.voicemail_url = self._GetRowValue(query_hash, row, "voicemail_url")

        parser_mediator.ProduceEventData(event_data)


sqlite.SQLiteParser.RegisterPlugin(AndroidBurnerPlugin)
