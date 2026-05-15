"""SQLite parser plugin for Google Chrome autofill database files.

The Google Chrome autofill database (Web Data) file is typically stored in:
  Web Data
"""

from dfdatetime import posix_time as dfdatetime_posix_time

from plaso.containers import events
from plaso.parsers import sqlite
from plaso.parsers.sqlite_plugins import interface


class ChromeAutofillEventData(events.EventData):
    """Chrome Autofill event data.

    Attributes:
      creation_time (dfdatetime.DateTimeValues): creation date and time of
          the autofill entry.
      field_name (str): name of form field.
      last_used_time (dfdatetime.DateTimeValues): last date and time
          the autofill entry was last used.
      query (str): SQL query that was used to obtain the event data.
      usage_count (int): count of times value has been used in field_name.
      value (str): value populated in form field.
    """

    DATA_TYPE = "chrome:autofill:entry"

    def __init__(self):
        """Initializes event data."""
        super().__init__(data_type=self.DATA_TYPE)
        self.creation_time = None
        self.field_name = None
        self.last_used_time = None
        self.query = None
        self.usage_count = None
        self.value = None


class ChromeAutofillPlugin(interface.SQLitePlugin):
    """SQLite parser plugin for Google Chrome autofill database files."""

    NAME = "chrome_autofill"
    DATA_FORMAT = "Google Chrome autofill SQLite database (Web Data) file"

    REQUIRED_STRUCTURE = {
        "autofill": frozenset(
            ["count", "date_created", "date_last_used", "name", "value"]
        )
    }

    QUERIES = [
        (
            (
                "SELECT count, date_created, date_last_used, name, value "
                "FROM autofill"
            ),
            "_ParseAutofillRow",
        )
    ]

    SCHEMAS = [
        {
            "autofill": (
                "CREATE TABLE autofill (name VARCHAR, value VARCHAR, value_lower "
                "VARCHAR, date_created INTEGER DEFAULT 0, date_last_used INTEGER "
                "DEFAULT 0, count INTEGER DEFAULT 1, PRIMARY KEY (name, value))"
            ),
            "autofill_model_type_state": (
                "CREATE TABLE autofill_model_type_state (id INTEGER PRIMARY KEY, "
                "value BLOB)"
            ),
            "autofill_profile_emails": (
                "CREATE TABLE autofill_profile_emails ( guid VARCHAR, email " "VARCHAR)"
            ),
            "autofill_profile_names": (
                "CREATE TABLE autofill_profile_names ( guid VARCHAR, first_name "
                "VARCHAR, middle_name VARCHAR, last_name VARCHAR, full_name "
                "VARCHAR)"
            ),
            "autofill_profile_phones": (
                "CREATE TABLE autofill_profile_phones ( guid VARCHAR, number "
                "VARCHAR)"
            ),
            "autofill_profiles": (
                "CREATE TABLE autofill_profiles ( guid VARCHAR PRIMARY KEY, "
                "company_name VARCHAR, street_address VARCHAR, dependent_locality "
                "VARCHAR, city VARCHAR, state VARCHAR, zipcode VARCHAR, "
                "sorting_code VARCHAR, country_code VARCHAR, date_modified INTEGER "
                "NOT NULL DEFAULT 0, origin VARCHAR DEFAULT '', language_code "
                "VARCHAR, use_count INTEGER NOT NULL DEFAULT 0, use_date INTEGER "
                "NOT NULL DEFAULT 0, validity_bitfield UNSIGNED NOT NULL DEFAULT 0)"
            ),
            "autofill_profiles_trash": (
                "CREATE TABLE autofill_profiles_trash ( guid VARCHAR)"
            ),
            "autofill_sync_metadata": (
                "CREATE TABLE autofill_sync_metadata (storage_key VARCHAR PRIMARY "
                "KEY NOT NULL,value BLOB)"
            ),
            "credit_cards": (
                "CREATE TABLE credit_cards ( guid VARCHAR PRIMARY KEY, name_on_card "
                "VARCHAR, expiration_month INTEGER, expiration_year INTEGER, "
                "card_number_encrypted BLOB, date_modified INTEGER NOT NULL DEFAULT "
                "0, origin VARCHAR DEFAULT '', use_count INTEGER NOT NULL DEFAULT "
                "0, use_date INTEGER NOT NULL DEFAULT 0, billing_address_id "
                "VARCHAR)"
            ),
            "keywords": (
                "CREATE TABLE keywords (id INTEGER PRIMARY KEY,short_name VARCHAR "
                "NOT NULL,keyword VARCHAR NOT NULL,favicon_url VARCHAR NOT NULL,url "
                "VARCHAR NOT NULL,safe_for_autoreplace INTEGER,originating_url "
                "VARCHAR,date_created INTEGER DEFAULT 0,usage_count INTEGER DEFAULT "
                "0,input_encodings VARCHAR,suggest_url VARCHAR,prepopulate_id "
                "INTEGER DEFAULT 0,created_by_policy INTEGER DEFAULT "
                "0,last_modified INTEGER DEFAULT 0,sync_guid VARCHAR,alternate_urls "
                "VARCHAR,image_url VARCHAR,search_url_post_params "
                "VARCHAR,suggest_url_post_params VARCHAR,image_url_post_params "
                "VARCHAR,new_tab_url VARCHAR,last_visited INTEGER DEFAULT 0)"
            ),
            "masked_credit_cards": (
                "CREATE TABLE masked_credit_cards (id VARCHAR,status "
                "VARCHAR,name_on_card VARCHAR,network VARCHAR,last_four "
                "VARCHAR,exp_month INTEGER DEFAULT 0,exp_year INTEGER DEFAULT 0, "
                "bank_name VARCHAR, type INTEGER DEFAULT 0)"
            ),
            "meta": (
                "CREATE TABLE meta(key LONGVARCHAR NOT NULL UNIQUE PRIMARY KEY, "
                "value LONGVARCHAR)"
            ),
            "payment_method_manifest": (
                "CREATE TABLE payment_method_manifest ( expire_date INTEGER NOT "
                "NULL DEFAULT 0, method_name VARCHAR, web_app_id VARCHAR)"
            ),
            "server_address_metadata": (
                "CREATE TABLE server_address_metadata (id VARCHAR NOT "
                "NULL,use_count INTEGER NOT NULL DEFAULT 0, use_date INTEGER NOT "
                "NULL DEFAULT 0, has_converted BOOL NOT NULL DEFAULT FALSE)"
            ),
            "server_addresses": (
                "CREATE TABLE server_addresses (id VARCHAR,company_name "
                "VARCHAR,street_address VARCHAR,address_1 VARCHAR,address_2 "
                "VARCHAR,address_3 VARCHAR,address_4 VARCHAR,postal_code "
                "VARCHAR,sorting_code VARCHAR,country_code VARCHAR,language_code "
                "VARCHAR, recipient_name VARCHAR, phone_number VARCHAR)"
            ),
            "server_card_metadata": (
                "CREATE TABLE server_card_metadata (id VARCHAR NOT NULL,use_count "
                "INTEGER NOT NULL DEFAULT 0, use_date INTEGER NOT NULL DEFAULT 0, "
                "billing_address_id VARCHAR)"
            ),
            "unmasked_credit_cards": (
                "CREATE TABLE unmasked_credit_cards (id "
                "VARCHAR,card_number_encrypted VARCHAR, use_count INTEGER NOT NULL "
                "DEFAULT 0, use_date INTEGER NOT NULL DEFAULT 0, unmask_date "
                "INTEGER NOT NULL DEFAULT 0)"
            ),
            "web_app_manifest_section": (
                "CREATE TABLE web_app_manifest_section ( expire_date INTEGER NOT "
                "NULL DEFAULT 0, id VARCHAR, min_version INTEGER NOT NULL DEFAULT "
                "0, fingerprints BLOB)"
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
          dfdatetime.PosixTime: date and time value or None if not available.
        """
        timestamp = self._GetRowValue(query_hash, row, value_name)
        if timestamp is None:
            return None

        return dfdatetime_posix_time.PosixTime(timestamp=timestamp)

    def _ParseAutofillRow(self, parser_mediator, query, row, **unused_kwargs):
        """Parses an autofill entry row.

        Args:
          parser_mediator (ParserMediator): mediates interactions between parsers
              and other components, such as storage and dfVFS.
          query (str): query that created the row.
          row (sqlite3.Row): row.
        """
        query_hash = hash(query)

        event_data = ChromeAutofillEventData()
        event_data.creation_time = self._GetDateTimeRowValue(
            query_hash, row, "date_created"
        )
        event_data.field_name = self._GetRowValue(query_hash, row, "name")
        event_data.last_used_time = self._GetDateTimeRowValue(
            query_hash, row, "date_last_used"
        )
        event_data.query = query
        event_data.usage_count = self._GetRowValue(query_hash, row, "count")
        event_data.value = self._GetRowValue(query_hash, row, "value")

        parser_mediator.ProduceEventData(event_data)


sqlite.SQLiteParser.RegisterPlugin(ChromeAutofillPlugin)
