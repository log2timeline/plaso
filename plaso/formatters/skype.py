# -*- coding: utf-8 -*-
"""Formatter for the Skype Main database events."""

from plaso.formatters import interface
from plaso.formatters import manager


class SkypeAccountFormatter(interface.ConditionalEventFormatter):
  """Formatter for Skype Account information."""

  DATA_TYPE = 'skype:event:account'

  FORMAT_STRING_PIECES = [u'{username}', u'[{email}]', u'Country: {country}']

  SOURCE_LONG = 'Skype Account'
  SOURCE_SHORT = 'LOG'


class SkypeChatFormatter(interface.ConditionalEventFormatter):
  """Formatter for Skype chat events."""

  DATA_TYPE = 'skype:event:chat'

  FORMAT_STRING_PIECES = [
      u'From: {from_account}',
      u'To: {to_account}',
      u'[{title}]',
      u'Message: [{text}]']

  FORMAT_STRING_SHORT_PIECES = [u'From: {from_account}', u' To: {to_account}']

  SOURCE_LONG = 'Skype Chat MSG'
  SOURCE_SHORT = 'LOG'


class SkypeSMSFormatter(interface.ConditionalEventFormatter):
  """Formatter for Skype SMS."""

  DATA_TYPE = 'skype:event:sms'

  FORMAT_STRING_PIECES = [u'To: {number}', u'[{text}]']

  SOURCE_LONG = 'Skype SMS'
  SOURCE_SHORT = 'LOG'


class SkypeCallFormatter(interface.ConditionalEventFormatter):
  """Formatter for Skype calls."""

  DATA_TYPE = 'skype:event:call'

  FORMAT_STRING_PIECES = [
      u'From: {src_call}',
      u'To: {dst_call}',
      u'[{call_type}]']

  SOURCE_LONG = 'Skype Call'
  SOURCE_SHORT = 'LOG'


class SkypeTransferFileFormatter(interface.ConditionalEventFormatter):
  """Formatter for Skype transfer files"""

  DATA_TYPE = 'skype:event:transferfile'

  FORMAT_STRING_PIECES = [
      u'Source: {source}',
      u'Destination: {destination}',
      u'File: {transferred_filename}',
      u'[{action_type}]']

  SOURCE_LONG = 'Skype Transfer Files'
  SOURCE_SHORT = 'LOG'


manager.FormattersManager.RegisterFormatters([
    SkypeAccountFormatter, SkypeChatFormatter, SkypeSMSFormatter,
    SkypeCallFormatter, SkypeTransferFileFormatter])
