# -*- coding: utf-8 -*-
"""The Basic Security Module (BSM) binary files event formatter."""

from __future__ import unicode_literals

from plaso.formatters import interface
from plaso.formatters import manager
from plaso.unix import bsmtoken


class BSMFormatter(interface.ConditionalEventFormatter):
  """Formatter for a BSM log entry."""

  DATA_TYPE = 'bsm:event'

  FORMAT_STRING_PIECES = [
      'Type: {event_type_string}',
      '({event_type})',
      'Return: {return_value}',
      'Information: {extra_tokens}']

  FORMAT_STRING_SHORT_PIECES = [
      'Type: {event_type}',
      'Return: {return_value}']

  SOURCE_LONG = 'BSM entry'
  SOURCE_SHORT = 'LOG'

  def __init__(self):
    """Initializes a BSM log entry format helper."""
    super(BSMFormatter, self).__init__()
    helper = interface.EnumerationEventFormatterHelper(
        default='UNKNOWN', input_attribute='event_type',
        output_attribute='event_type_string', values=bsmtoken.BSM_AUDIT_EVENT)

    self.helpers.append(helper)


manager.FormattersManager.RegisterFormatter(BSMFormatter)
