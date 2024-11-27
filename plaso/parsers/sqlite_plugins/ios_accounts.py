# -*- coding: utf-8 -*-
"""SQLite parser plugin for iOS accounts (Accounts3.db) database files."""

from dfdatetime import cocoa_time as dfdatetime_cocoa_time

from plaso.containers import events
from plaso.parsers import sqlite
from plaso.parsers.sqlite_plugins import interface


class IOSAccounts(events.EventData):
  """iOS accounts event data.

  Attributes:
      date (dfdatetime.DateTimeValues): date and time the account 
          was created.
      account_type (str): account type.
      username (str): user name.
      identifier (str): identifier.
      owning_bundle_id (str): owning bundle identifier of the app 
          managing the account.
  """

  DATA_TYPE = 'ios:accounts:account'

  def __init__(self):
      """Initializes event data."""
      super(IOSAccounts, self).__init__(data_type=self.DATA_TYPE)
      self.date = None
      self.account_type = None
      self.username = None
      self.identifier = None
      self.owning_bundle_id = None

class IOSAccountsPlugin(interface.SQLitePlugin):
  """SQLite parser plugin for iOS accounts (Accounts3.db) database files."""

  NAME = 'ios_accounts'
  DATA_FORMAT = 'iOS accounts SQLite database (Accounts3.db) file'

  REQUIRED_STRUCTURE = {
      'ZACCOUNT': frozenset([
          'ZACCOUNTTYPE', 'ZDATE', 'ZUSERNAME', 'ZIDENTIFIER', 
          'ZOWNINGBUNDLEID']),
      'ZACCOUNTTYPE': frozenset([
          'Z_PK', 'ZACCOUNTTYPEDESCRIPTION'])
  }

  QUERIES = [((
      'SELECT ZACCOUNT.ZDATE, ZACCOUNTTYPE.ZACCOUNTTYPEDESCRIPTION, '
      'ZACCOUNT.ZUSERNAME, ZACCOUNT.ZIDENTIFIER, ZACCOUNT.ZOWNINGBUNDLEID '
      'FROM ZACCOUNT LEFT JOIN ZACCOUNTTYPE '
      'ON ZACCOUNT.ZACCOUNTTYPE = ZACCOUNTTYPE.Z_PK'),
      'ParseAccountRow')]

  SCHEMAS = {
      'ZACCOUNT': (
          'CREATE TABLE ZACCOUNT (Z_PK INTEGER PRIMARY KEY, Z_ENT INTEGER, '
          'Z_OPT INTEGER, ZACTIVE INTEGER, ZAUTHENTICATED INTEGER, '
          'ZSUPPORTSAUTHENTICATION INTEGER, ZVISIBLE INTEGER, '
          'ZACCOUNTTYPE INTEGER, ZPARENTACCOUNT INTEGER, '
          'ZDATE TIMESTAMP, ZLASTCREDENTIALRENEWALREJECTIONDATE TIMESTAMP, '
          'ZACCOUNTDESCRIPTION TEXT, ZAUTHENTICATIONTYPE TEXT, '
          'ZCREDENTIALTYPE TEXT, ZIDENTIFIER TEXT, ZOWNINGBUNDLEID TEXT, '
          'ZUSERNAME TEXT, ZDATACLASSPROPERTIES BLOB)'),
      'ZACCOUNTTYPE': (
          'CREATE TABLE ZACCOUNTTYPE (Z_PK INTEGER PRIMARY KEY, '
          'Z_ENT INTEGER, Z_OPT INTEGER, ZENCRYPTACCOUNTPROPERTIES INTEGER, '
          'ZOBSOLETE INTEGER, ZSUPPORTSAUTHENTICATION INTEGER, '
          'ZSUPPORTSMULTIPLEACCOUNTS INTEGER, ZVISIBILITY INTEGER, '
          'ZACCOUNTTYPEDESCRIPTION TEXT, ZCREDENTIALPROTECTIONPOLICY TEXT, '
          'ZCREDENTIALTYPE TEXT, ZIDENTIFIER TEXT, ZOWNINGBUNDLEID TEXT)')}

  REQUIRES_SCHEMA_MATCH = False

  def _GetTimeRowValue(self, query_hash, row, value_name):
      """Retrieves a date and time value from the row.

      Args:
          query_hash (int): hash of the query, that uniquely 
            identifies the query that produced the row.
          row (sqlite3.Row): row.
          value_name (str): name of the value.

      Returns:
          dfdatetime.CocoaTime: date and time value or None if not available.
      """
      timestamp = self._GetRowValue(query_hash, row, value_name)
      if timestamp is None:
          return None

      return dfdatetime_cocoa_time.CocoaTime(timestamp=timestamp)

  # pylint: disable=unused-argument
  def ParseAccountRow(
      self, parser_mediator, query, row, **unused_kwargs):
      """Parses an account row.

      Args:
          parser_mediator (ParserMediator): mediates interactions between
            parsers and other components, such as storage and dfVFS.
          query (str): query that created the row.
          row (sqlite3.Row): row.
      """
      query_hash = hash(query)

      event_data = IOSAccounts()
      event_data.date = self._GetTimeRowValue(query_hash, row, 'ZDATE')
      event_data.account_type = self._GetRowValue(query_hash, 
          row, 'ZACCOUNTTYPEDESCRIPTION')
      event_data.username = self._GetRowValue(query_hash, row, 'ZUSERNAME')
      event_data.identifier = self._GetRowValue(query_hash, row, 
          'ZIDENTIFIER')
      event_data.owning_bundle_id = self._GetRowValue(query_hash, row,
          'ZOWNINGBUNDLEID')

      parser_mediator.ProduceEventData(event_data)


sqlite.SQLiteParser.RegisterPlugin(IOSAccountsPlugin)
