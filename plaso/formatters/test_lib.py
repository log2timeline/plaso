# -*- coding: utf-8 -*-
"""Formatter related functions and classes for testing."""

from plaso.formatters import interface


class TestEventFormatter(interface.EventFormatter):
  """Class to define a formatter for a test event."""
  DATA_TYPE = 'test:event'
  FORMAT_STRING = u'{text}'

  SOURCE_SHORT = 'FILE'
  SOURCE_LONG = 'Weird Log File'
