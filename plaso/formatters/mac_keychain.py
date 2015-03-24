# -*- coding: utf-8 -*-
"""The Mac OS X keychain password database file event formatter."""

from plaso.formatters import interface
from plaso.formatters import manager


class KeychainApplicationRecordFormatter(interface.ConditionalEventFormatter):
  """Formatter for a keychain application record event."""

  DATA_TYPE = 'mac:keychain:application'

  FORMAT_STRING_PIECES = [
      u'Name: {entry_name}',
      u'Account: {account_name}']

  FORMAT_STRING_SHORT_PIECES = [u'{entry_name}']

  SOURCE_LONG = 'Keychain Application password'
  SOURCE_SHORT = 'LOG'


class KeychainInternetRecordFormatter(interface.ConditionalEventFormatter):
  """Formatter for a keychain Internet record event."""

  DATA_TYPE = 'mac:keychain:internet'

  FORMAT_STRING_PIECES = [
      u'Name: {entry_name}',
      u'Account: {account_name}',
      u'Where: {where}',
      u'Protocol: {protocol}',
      u'({type_protocol})']

  FORMAT_STRING_SHORT_PIECES = [u'{entry_name}']

  SOURCE_LONG = 'Keychain Internet password'
  SOURCE_SHORT = 'LOG'


manager.FormattersManager.RegisterFormatters([
    KeychainApplicationRecordFormatter, KeychainInternetRecordFormatter])
