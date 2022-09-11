# -*- coding: utf-8 -*-
"""Plist parser plugin for Apple Account plist files."""

from dfdatetime import semantic_time as dfdatetime_semantic_time
from dfdatetime import time_elements as dfdatetime_time_elements

from plaso.containers import events
from plaso.containers import time_events
from plaso.lib import definitions
from plaso.parsers import plist
from plaso.parsers.plist_plugins import interface


class AppleAccountEventData(events.EventData):
  """Apple account event data.

  Attributes:
    account_name (str): name of the account.
    first_name (str): first name.
    last_name (str): last name.
  """

  DATA_TYPE = 'macos:apple_account:entry'

  def __init__(self):
    """Initializes event data."""
    super(AppleAccountEventData, self).__init__(data_type=self.DATA_TYPE)
    self.account_name = None
    self.first_name = None
    self.last_name = None


class AppleAccountPlistPlugin(interface.PlistPlugin):
  """Plist parser plugin for Apple Account plist files.

  Further details about fields within the key:
    Accounts: account name.
    FirstName: first name associated with the account.
    LastName: family name associate with the account.
    CreationDate: timestamp when the account was configured in the system.
    LastSuccessfulConnect: last time when the account was connected.
    ValidationDate: last time when the account was validated.
  """

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
    accounts = match.get('Accounts', {})
    for account_name, account in accounts.items():
      event_data = AppleAccountEventData()
      event_data.account_name = account_name
      event_data.first_name = account.get('FirstName', None)
      event_data.last_name = account.get('LastName', None)

      datetime_value = account.get('CreationDate', None)
      if not datetime_value:
        date_time = dfdatetime_semantic_time.NotSet()
      else:
        date_time = dfdatetime_time_elements.TimeElements()
        date_time.CopyFromDatetime(datetime_value)

      event = time_events.DateTimeValuesEvent(
          date_time, definitions.TIME_DESCRIPTION_CREATION)
      parser_mediator.ProduceEventWithEventData(event, event_data)

      datetime_value = account.get('LastSuccessfulConnect', None)
      if datetime_value:
        date_time = dfdatetime_time_elements.TimeElements()
        date_time.CopyFromDatetime(datetime_value)

        event = time_events.DateTimeValuesEvent(
            date_time, definitions.TIME_DESCRIPTION_CONNECTION_ESTABLISHED)
        parser_mediator.ProduceEventWithEventData(event, event_data)

      datetime_value = account.get('ValidationDate', None)
      if datetime_value:
        date_time = dfdatetime_time_elements.TimeElements()
        date_time.CopyFromDatetime(datetime_value)

        event = time_events.DateTimeValuesEvent(
            date_time, definitions.TIME_DESCRIPTION_VALIDATION)
        parser_mediator.ProduceEventWithEventData(event, event_data)


plist.PlistParser.RegisterPlugin(AppleAccountPlistPlugin)
