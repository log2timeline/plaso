# -*- coding: utf-8 -*-
"""This file contains a Apple Account plist plugin in Plaso."""

from plaso.events import plist_event
from plaso.lib import errors
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
      parser_mediator: A parser mediator object (instance of ParserMediator).
      plist_name: name of the plist file.
      top_level: dictionary with the plist file parsed.
    """
    if not plist_name.startswith(self.PLIST_PATH):
      raise errors.WrongPlistPlugin(self.NAME, plist_name)
    super(AppleAccountPlugin, self).Process(
        parser_mediator, plist_name=self.PLIST_PATH, top_level=top_level)

  def GetEntries(self, parser_mediator, match=None, **unused_kwargs):
    """Extracts relevant Apple Account entries.

    Args:
      parser_mediator: A parser mediator object (instance of ParserMediator).
      match: Optional dictionary containing keys extracted from PLIST_KEYS.
    """
    root = u'/Accounts'

    if not u'Accounts' in match:
      return

    for name_account, account in match[u'Accounts'].iteritems():
      general_description = u'{0:s} ({1:s} {2:s})'.format(
          name_account, account.get(u'FirstName', u'<FirstName>'),
          account.get(u'LastName', u'<LastName>'))
      key = name_account
      description = u'Configured Apple account {0:s}'.format(
          general_description)
      if u'CreationDate' in account:
        event_object = plist_event.PlistEvent(
            root, key, account[u'CreationDate'], description)
        parser_mediator.ProduceEvent(event_object)

      if u'LastSuccessfulConnect' in account:
        description = u'Connected Apple account {0:s}'.format(
            general_description)
        event_object = plist_event.PlistEvent(
            root, key, account[u'LastSuccessfulConnect'], description)
        parser_mediator.ProduceEvent(event_object)

      if u'ValidationDate' in account:
        description = u'Last validation Apple account {0:s}'.format(
            general_description)
        event_object = plist_event.PlistEvent(
            root, key, account[u'ValidationDate'], description)
        parser_mediator.ProduceEvent(event_object)


plist.PlistParser.RegisterPlugin(AppleAccountPlugin)
