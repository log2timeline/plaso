# -*- coding: utf-8 -*-
"""The macOS TCC event formatter."""

from __future__ import unicode_literals

from plaso.formatters import interface
from plaso.formatters import manager


class MacOSTCCFormatter(interface.ConditionalEventFormatter):
  """Formatter for macOS TCC events."""

  DATA_TYPE = 'macos:tcc_entry'

  FORMAT_STRING_PIECES = [
      'Service: {service}',
      'Client: {client}',
      'Allowed: {allowed}',
      'Prompt count: {prompt_count}'
    ]

  FORMAT_STRING_SHORT_PIECES = ['{service}:', '{client}']

  SOURCE_LONG = 'macOS Transparenty, Control and Consent logs'
  SOURCE_SHORT = 'macOS TCC'

  _ALLOWED = {
      0: False,
      1: True
  }

  def __init__(self):
    """Initializes an iMessage chat event format helper."""
    super(MacOSTCCFormatter, self).__init__()
    helper = interface.EnumerationEventFormatterHelper(
        default='UNKNOWN', input_attribute='allowed',
        output_attribute='allowed', values=self._ALLOWED)

    self.helpers.append(helper)


manager.FormattersManager.RegisterFormatter(MacOSTCCFormatter)
