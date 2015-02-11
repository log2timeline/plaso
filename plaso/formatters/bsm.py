# -*- coding: utf-8 -*-
"""Formatter for Basic Security Module binary files."""

from plaso.formatters import interface
from plaso.formatters import manager


class BSMFormatter(interface.ConditionalEventFormatter):
  """Formatter for an BSM log entry."""

  DATA_TYPE = 'bsm:event'

  FORMAT_STRING_PIECES = [
      u'Type: {event_type}',
      u'Information: {extra_tokens}']

  FORMAT_STRING_SHORT_PIECES = [
      u'Type: {event_type}']

  SOURCE_LONG = 'BSM entry'
  SOURCE_SHORT = 'LOG'


class MacBSMFormatter(interface.ConditionalEventFormatter):
  """Formatter for a Mac OS X BSM log entry."""

  DATA_TYPE = 'mac:bsm:event'

  FORMAT_STRING_PIECES = [
      u'Type: {event_type}',
      u'Return: {return_value}',
      u'Information: {extra_tokens}']

  FORMAT_STRING_SHORT_PIECES = [
      u'Type: {event_type}',
      u'Return: {return_value}']

  SOURCE_LONG = 'BSM entry'
  SOURCE_SHORT = 'LOG'


manager.FormattersManager.RegisterFormatters([
    BSMFormatter, MacBSMFormatter])
