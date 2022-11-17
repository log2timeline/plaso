# -*- coding: utf-8 -*-
"""Plist parser plugin for Apple Account plist files.

Fields within the plist key: com.apple.coreservices.appleidauthenticationinfo
  Accounts: account name.
  FirstName: first name associated with the account.
  LastName: last (or family) name associate with the account.
  CreationDate: timestamp when the account was configured in the system.
  LastSuccessfulConnect: last time when the account was connected.
  ValidationDate: last time when the account was validated.
"""

from plaso.containers import events
from plaso.parsers import plist
from plaso.parsers.plist_plugins import interface


class AppleAccountEventData(events.EventData):
  """Apple account event data.

  Attributes:
    account_name (str): name of the account.
    creation_time (dfdatetime.DateTimeValues): date and time the Apple account
        was created (configured) on the system.
    first_name (str): first name.
    last_connected_time (dfdatetime.DateTimeValues): last date and time
        the system successfully connected to the Apple account.
    last_name (str): last (or family) name.
    validation_time (dfdatetime.DateTimeValues): date and time the Apple account
        was validated.
  """

  DATA_TYPE = 'macos:apple_account:entry'

  def __init__(self):
    """Initializes event data."""
    super(AppleAccountEventData, self).__init__(data_type=self.DATA_TYPE)
    self.account_name = None
    self.creation_time = None
    self.first_name = None
    self.last_connected_time = None
    self.last_name = None
    self.validation_time = None


class AppleAccountPlistPlugin(interface.PlistPlugin):
  """Plist parser plugin for Apple Account plist files."""

  NAME = 'apple_id'
  DATA_FORMAT = 'Apple account information plist file'

  PLIST_PATH_FILTERS = frozenset([
      interface.PrefixPlistPathFilter(
          'com.apple.coreservices.appleidauthenticationinfo')])

  PLIST_KEYS = frozenset(['AuthCertificates', 'AccessorVersions', 'Accounts'])

  # pylint: disable=arguments-differ
  def _ParsePlist(self, parser_mediator, match=None, **unused_kwargs):
    """Extracts relevant Apple Account entries.

    Args:
      parser_mediator (ParserMediator): mediates interactions between parsers
          and other components, such as storage and dfVFS.
      match (Optional[dict[str: object]]): keys extracted from PLIST_KEYS.
    """
    for account_name, plist_key in match.get('Accounts', {}).items():
      event_data = AppleAccountEventData()
      event_data.account_name = account_name
      event_data.creation_time = self._GetDateTimeValueFromPlistKey(
          plist_key, 'CreationDate')
      event_data.first_name = plist_key.get('FirstName', None)
      event_data.last_connected_time = self._GetDateTimeValueFromPlistKey(
          plist_key, 'LastSuccessfulConnect')
      event_data.last_name = plist_key.get('LastName', None)
      event_data.validation_time = self._GetDateTimeValueFromPlistKey(
          plist_key, 'ValidationDate')

      parser_mediator.ProduceEventData(event_data)


plist.PlistParser.RegisterPlugin(AppleAccountPlistPlugin)
