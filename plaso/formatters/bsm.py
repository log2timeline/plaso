# -*- coding: utf-8 -*-
"""The Basic Security Module (BSM) binary files event formatter."""

from __future__ import unicode_literals

from plaso.formatters import interface
from plaso.formatters import manager


class BSMFormatter(interface.ConditionalEventFormatter):
  """Formatter for an BSM log entry."""

  DATA_TYPE = 'bsm:event'

  FORMAT_STRING_PIECES = [
      'Type: {event_type}',
      'Information: {extra_tokens}']

  FORMAT_STRING_SHORT_PIECES = [
      'Type: {event_type}']

  SOURCE_LONG = 'BSM entry'
  SOURCE_SHORT = 'LOG'


class MacBSMFormatter(interface.ConditionalEventFormatter):
  """Formatter for a Mac OS X BSM log entry."""

  DATA_TYPE = 'mac:bsm:event'

  FORMAT_STRING_PIECES = [
      'Type: {event_type}',
      'Return: {return_value}',
      'Information: {extra_tokens}']

  FORMAT_STRING_SHORT_PIECES = [
      'Type: {event_type}',
      'Return: {return_value}']

  SOURCE_LONG = 'BSM entry'
  SOURCE_SHORT = 'LOG'


manager.FormattersManager.RegisterFormatters([
    BSMFormatter, MacBSMFormatter])
