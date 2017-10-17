# -*- coding: utf-8 -*-
"""The Skype main database event formatter."""

from __future__ import unicode_literals

from plaso.formatters import interface
from plaso.formatters import manager


class SkypeAccountFormatter(interface.ConditionalEventFormatter):
  """Formatter for a Skype account event."""

  DATA_TYPE = 'skype:event:account'

  FORMAT_STRING_PIECES = [
      '{username}',
      '[{email}]',
      'Country: {country}']

  SOURCE_LONG = 'Skype Account'
  SOURCE_SHORT = 'LOG'


class SkypeChatFormatter(interface.ConditionalEventFormatter):
  """Formatter for a Skype chat message event."""

  DATA_TYPE = 'skype:event:chat'

  FORMAT_STRING_PIECES = [
      'From: {from_account}',
      'To: {to_account}',
      '[{title}]',
      'Message: [{text}]']

  FORMAT_STRING_SHORT_PIECES = [
      'From: {from_account}',
      'To: {to_account}']

  SOURCE_LONG = 'Skype Chat MSG'
  SOURCE_SHORT = 'LOG'


class SkypeSMSFormatter(interface.ConditionalEventFormatter):
  """Formatter for a Skype SMS event."""

  DATA_TYPE = 'skype:event:sms'

  FORMAT_STRING_PIECES = [
      'To: {number}',
      '[{text}]']

  SOURCE_LONG = 'Skype SMS'
  SOURCE_SHORT = 'LOG'


class SkypeCallFormatter(interface.ConditionalEventFormatter):
  """Formatter for a Skype call event."""

  DATA_TYPE = 'skype:event:call'

  FORMAT_STRING_PIECES = [
      'From: {src_call}',
      'To: {dst_call}',
      '[{call_type}]']

  SOURCE_LONG = 'Skype Call'
  SOURCE_SHORT = 'LOG'


class SkypeTransferFileFormatter(interface.ConditionalEventFormatter):
  """Formatter for a Skype transfer file event."""

  DATA_TYPE = 'skype:event:transferfile'

  FORMAT_STRING_PIECES = [
      'Source: {source}',
      'Destination: {destination}',
      'File: {transferred_filename}',
      '[{action_type}]']

  SOURCE_LONG = 'Skype Transfer Files'
  SOURCE_SHORT = 'LOG'


manager.FormattersManager.RegisterFormatters([
    SkypeAccountFormatter, SkypeChatFormatter, SkypeSMSFormatter,
    SkypeCallFormatter, SkypeTransferFileFormatter])
