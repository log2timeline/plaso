# -*- coding: utf-8 -*-
"""SQLite parser plugin for MacOS Accounts database files."""

from dfdatetime import cocoa_time as dfdatetime_cocoa_time

from plaso.containers import events
from plaso.parsers import sqlite
from plaso.parsers.sqlite_plugins import interface


class MacOSAccountEventData(events.EventData):
  """MacOS Account event data.

  Attributes:
    account_description (str): description of the account.
    account_type (str): type of account.
    creation_time (dfdatetime.DateTimeValues): date and time the account
        was created.
    identifier (str): account identifier.
    modification_time (dfdatetime.DateTimeValues): date and time the account
        was last modified.
    query (str): SQL query that was used to obtain the event data.
    username (str): username associated with the account.
    is_active (int): whether the account is active (1) or not (0).
    is_authenticated (int): whether the account is authenticated (1) or not (0).
    is_visible (int): whether the account is visible (1) or not (0).
    auth_type (int): authentication type.
    credential_type (int): credential type.
    owning_bundle (str): bundle identifier of the owning application.
    last_credential_rejection_time (dfdatetime.DateTimeValues): date and time 
        the last credential renewal was rejected.
  """

  DATA_TYPE = 'macos:accounts:entry'

  def __init__(self):
    """Initializes event data."""
    super(MacOSAccountEventData, self).__init__(data_type=self.DATA_TYPE)
    self.account_description = None
    self.account_type = None
    self.creation_time = None
    self.identifier = None
    self.modification_time = None
    self.query = None
    self.username = None
    self.is_active = None
    self.is_authenticated = None
    self.is_visible = None
    self.auth_type = None
    self.credential_type = None
    self.owning_bundle = None
    self.last_credential_rejection_time = None


class MacOSAccountsPlugin(interface.SQLitePlugin):
  """SQLite parser plugin for MacOS Accounts database files.

  The MacOS Accounts database file is typically stored in:
  /Users/<username>/Library/Accounts/Accounts4.sqlite
  """

  NAME = 'macos_accounts'
  DATA_FORMAT = 'MacOS Accounts SQLite database (Accounts4.sqlite) file'

  REQUIRED_STRUCTURE = {
      'ZACCOUNT': frozenset([
          'Z_PK', 'ZACCOUNTDESCRIPTION', 'ZACCOUNTTYPE', 'ZDATE', 
          'ZIDENTIFIER', 'ZUSERNAME', 'ZACTIVE', 'ZAUTHENTICATED',
          'ZVISIBLE', 'ZCREDENTIALTYPE', 'ZOWNINGBUNDLEID',
          'ZLASTCREDENTIALRENEWALREJECTIONDATE']),
      'ZACCOUNTTYPE': frozenset([
          'Z_PK', 'ZACCOUNTTYPEDESCRIPTION', 'ZIDENTIFIER'])}

  QUERIES = [
      (('SELECT ZACCOUNT.Z_PK, ZACCOUNT.ZACCOUNTDESCRIPTION, '
        'ZACCOUNTTYPE.ZACCOUNTTYPEDESCRIPTION AS account_type, '
        'ZACCOUNT.ZDATE AS creation_time, ZACCOUNT.ZIDENTIFIER, '
        'ZACCOUNT.ZUSERNAME, ZACCOUNT.ZACTIVE AS is_active, '
        'ZACCOUNT.ZAUTHENTICATED AS is_authenticated, '
        'ZACCOUNT.ZVISIBLE AS is_visible, ZACCOUNT.ZAUTHENTICATIONTYPE AS auth_type, '
        'ZACCOUNT.ZCREDENTIALTYPE AS credential_type, '
        'ZACCOUNT.ZOWNINGBUNDLEID AS owning_bundle, '
        'ZACCOUNT.ZLASTCREDENTIALRENEWALREJECTIONDATE AS last_cred_rejection_date '
        'FROM ZACCOUNT '
        'LEFT JOIN ZACCOUNTTYPE ON ZACCOUNT.ZACCOUNTTYPE = ZACCOUNTTYPE.Z_PK'),
       'ParseAccountRow')]

  SCHEMAS = [{
      'ZACCOUNT': (
          'CREATE TABLE ZACCOUNT ( Z_PK INTEGER PRIMARY KEY, Z_ENT INTEGER, '
          'Z_OPT INTEGER, ZACCOUNTTYPE INTEGER, ZACTIVE INTEGER, '
          'ZAUTHENTICATED INTEGER, ZVISIBLE INTEGER, ZCREDENTIALTYPE INTEGER, '
          'ZAUTHENTICATIONTYPE INTEGER, ZACCOUNTDESCRIPTION VARCHAR, ZIDENTIFIER VARCHAR, '
          'ZOWNINGBUNDLEID VARCHAR, ZPARENTACCOUNT VARCHAR, ZUSERNAME VARCHAR, '
          'ZDATE TIMESTAMP, ZLASTCREDENTIALRENEWALREJECTIONDATE TIMESTAMP )'),
      'ZACCOUNTTYPE': (
          'CREATE TABLE ZACCOUNTTYPE ( Z_PK INTEGER PRIMARY KEY, Z_ENT INTEGER, '
          'Z_OPT INTEGER, ZSUPPORTSAUTHENTICATION INTEGER, '
          'ZSUPPORTSMULTIPLEACCOUNTS INTEGER, ZACCOUNTTYPEDESCRIPTION VARCHAR, '
          'ZIDENTIFIER VARCHAR )')}]

  def _GetDateTimeRowValue(self, query_hash, row, value_name):
    """Retrieves a date and time value from the row.

    Args:
      query_hash (int): hash of the query, that uniquely identifies the query
          that produced the row.
      row (sqlite3.Row): row.
      value_name (str): name of the value.

    Returns:
      dfdatetime.CocoaTime: date and time value or None if not available.
    """
    timestamp = self._GetRowValue(query_hash, row, value_name)
    if timestamp is None:
      return None

    return dfdatetime_cocoa_time.CocoaTime(timestamp=timestamp)

  def ParseAccountRow(self, parser_mediator, query, row, **unused_kwargs):
    """Parses an account row.

    Args:
      parser_mediator (ParserMediator): mediates interactions between parsers
          and other components, such as storage and dfVFS.
      query (str): query that created the row.
      row (sqlite3.Row): row.
    """
    query_hash = hash(query)

    event_data = MacOSAccountEventData()
    event_data.account_description = self._GetRowValue(
        query_hash, row, 'ZACCOUNTDESCRIPTION')
    event_data.account_type = self._GetRowValue(query_hash, row, 'account_type')
    event_data.creation_time = self._GetDateTimeRowValue(
        query_hash, row, 'creation_time')
    event_data.identifier = self._GetRowValue(query_hash, row, 'ZIDENTIFIER')
    event_data.query = query
    event_data.username = self._GetRowValue(query_hash, row, 'ZUSERNAME')
    
    # Add new fields
    event_data.is_active = self._GetRowValue(query_hash, row, 'is_active')
    event_data.is_authenticated = self._GetRowValue(query_hash, row, 'is_authenticated')
    event_data.is_visible = self._GetRowValue(query_hash, row, 'is_visible')
    event_data.auth_type = self._GetRowValue(query_hash, row, 'auth_type')
    event_data.credential_type = self._GetRowValue(query_hash, row, 'credential_type')
    event_data.owning_bundle = self._GetRowValue(query_hash, row, 'owning_bundle')
    event_data.last_credential_rejection_time = self._GetDateTimeRowValue(
        query_hash, row, 'last_cred_rejection_date')

    parser_mediator.ProduceEventData(event_data)


sqlite.SQLiteParser.RegisterPlugin(MacOSAccountsPlugin)
