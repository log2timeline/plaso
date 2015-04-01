# -*- coding: utf-8 -*-
"""Output related functions and classes for testing."""

import unittest

from plaso.formatters import mediator as formatters_mediator


class OutputModuleTestCase(unittest.TestCase):
  """The unit test case for a output module."""

  # Show full diff results, part of TestCase so does not follow our naming
  # conventions.
  maxDiff = None

  def setUp(self):
    """Sets up the objects used throughout a single test."""
    self._formatter_mediator = formatters_mediator.FormatterMediator()
