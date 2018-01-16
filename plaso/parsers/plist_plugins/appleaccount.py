# -*- coding: utf-8 -*-
"""Apple Account plist plugin."""

from __future__ import unicode_literals

from plaso.containers import plist_event
from plaso.containers import time_events
from plaso.lib import definitions
from plaso.lib import errors
from plaso.parsers import plist
from plaso.parsers.plist_plugins import interface


class AppleAccountPlugin(interface.PlistPlugin):
  """Basic plugin to extract the apple account information.

  Further details about fields within the key:
    Accounts: account name.
    FirstName: first name associated with the account.
    LastName: family name associate with the account.
    CreationDate: timestamp when the account was configured in the system.
    LastSuccessfulConnect: last time when the account was connected.
    ValidationDate: last time when the account was validated.
  """

  NAME = 'apple_id'
  DESCRIPTION = 'Parser for Apple account information plist files.'

  PLIST_PATH = 'com.apple.coreservices.appleidauthenticationinfo'
  PLIST_KEYS = frozenset(
      ['AuthCertificates', 'AccessorVersions', 'Accounts'])

  def Process(self, parser_mediator, plist_name, top_level, **kwargs):
    """Check if it is a valid Apple account plist file name.

    Args:
      parser_mediator (ParserMediator): mediates interactions between parsers
          and other components, such as storage and dfvfs.
      plist_name (str): name of the plist.
      top_level (dict[str, object]): plist top-level key.
    """
    if not plist_name.startswith(self.PLIST_PATH):
      raise errors.WrongPlistPlugin(self.NAME, plist_name)
    super(AppleAccountPlugin, self).Process(
        parser_mediator, plist_name=self.PLIST_PATH, top_level=top_level)

  # pylint: disable=arguments-differ
  def GetEntries(self, parser_mediator, match=None, **unused_kwargs):
    """Extracts relevant Apple Account entries.

    Args:
      parser_mediator (ParserMediator): mediates interactions between parsers
          and other components, such as storage and dfvfs.
      match (Optional[dict[str: object]]): keys extracted from PLIST_KEYS.
    """
    accounts = match.get('Accounts', {})
    for name_account, account in iter(accounts.items()):
      first_name = account.get('FirstName', '<FirstName>')
      last_name = account.get('LastName', '<LastName>')
      general_description = '{0:s} ({1:s} {2:s})'.format(
          name_account, first_name, last_name)

      event_data = plist_event.PlistTimeEventData()
      event_data.key = name_account
      event_data.root = '/Accounts'

      datetime_value = account.get('CreationDate', None)
      if datetime_value:
        event_data.desc = 'Configured Apple account {0:s}'.format(
            general_description)

        event = time_events.PythonDatetimeEvent(
            datetime_value, definitions.TIME_DESCRIPTION_WRITTEN)
        parser_mediator.ProduceEventWithEventData(event, event_data)

      datetime_value = account.get('LastSuccessfulConnect', None)
      if datetime_value:
        event_data.desc = 'Connected Apple account {0:s}'.format(
            general_description)

        event = time_events.PythonDatetimeEvent(
            datetime_value, definitions.TIME_DESCRIPTION_WRITTEN)
        parser_mediator.ProduceEventWithEventData(event, event_data)

      datetime_value = account.get('ValidationDate', None)
      if datetime_value:
        event_data.desc = 'Last validation Apple account {0:s}'.format(
            general_description)

        event = time_events.PythonDatetimeEvent(
            datetime_value, definitions.TIME_DESCRIPTION_WRITTEN)
        parser_mediator.ProduceEventWithEventData(event, event_data)


plist.PlistParser.RegisterPlugin(AppleAccountPlugin)
