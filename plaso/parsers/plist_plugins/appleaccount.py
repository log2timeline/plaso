# -*- coding: utf-8 -*-
"""Apple Account plist plugin."""

from dfdatetime import posix_time as dfdatetime_posix_time

from plaso.containers import plist_event
from plaso.containers import time_events
from plaso.lib import definitions
from plaso.lib import errors
from plaso.lib import timelib
from plaso.parsers import plist
from plaso.parsers.plist_plugins import interface


__author__ = 'Joaquin Moreno Garijo (Joaquin.MorenoGarijo.2013@live.rhul.ac.uk)'


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

  NAME = u'apple_id'
  DESCRIPTION = u'Parser for Apple account information plist files.'

  PLIST_PATH = u'com.apple.coreservices.appleidauthenticationinfo'
  PLIST_KEYS = frozenset(
      [u'AuthCertificates', u'AccessorVersions', u'Accounts'])

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

  def GetEntries(self, parser_mediator, match=None, **unused_kwargs):
    """Extracts relevant Apple Account entries.

    Args:
      parser_mediator (ParserMediator): mediates interactions between parsers
          and other components, such as storage and dfvfs.
      match (Optional[dict[str: object]]): keys extracted from PLIST_KEYS.
    """
    accounts = match.get(u'Accounts', {})
    for name_account, account in iter(accounts.items()):
      first_name = account.get(u'FirstName', u'<FirstName>')
      last_name = account.get(u'LastName', u'<LastName>')
      general_description = u'{0:s} ({1:s} {2:s})'.format(
          name_account, first_name, last_name)

      event_data = plist_event.PlistTimeEventData()
      event_data.key = name_account
      event_data.root = u'/Accounts'

      datetime_value = account.get(u'CreationDate', None)
      if datetime_value:
        event_data.desc = u'Configured Apple account {0:s}'.format(
            general_description)

        timestamp = timelib.Timestamp.FromPythonDatetime(datetime_value)
        date_time = dfdatetime_posix_time.PosixTimeInMicroseconds(
            timestamp=timestamp)
        event = time_events.DateTimeValuesEvent(
            date_time, definitions.TIME_DESCRIPTION_WRITTEN)
        parser_mediator.ProduceEventWithEventData(event, event_data)

      datetime_value = account.get(u'LastSuccessfulConnect', None)
      if datetime_value:
        event_data.desc = u'Connected Apple account {0:s}'.format(
            general_description)

        timestamp = timelib.Timestamp.FromPythonDatetime(datetime_value)
        date_time = dfdatetime_posix_time.PosixTimeInMicroseconds(
            timestamp=timestamp)
        event = time_events.DateTimeValuesEvent(
            date_time, definitions.TIME_DESCRIPTION_WRITTEN)
        parser_mediator.ProduceEventWithEventData(event, event_data)

      datetime_value = account.get(u'ValidationDate', None)
      if datetime_value:
        event_data.desc = u'Last validation Apple account {0:s}'.format(
            general_description)

        timestamp = timelib.Timestamp.FromPythonDatetime(datetime_value)
        date_time = dfdatetime_posix_time.PosixTimeInMicroseconds(
            timestamp=timestamp)
        event = time_events.DateTimeValuesEvent(
            date_time, definitions.TIME_DESCRIPTION_WRITTEN)
        parser_mediator.ProduceEventWithEventData(event, event_data)


plist.PlistParser.RegisterPlugin(AppleAccountPlugin)
