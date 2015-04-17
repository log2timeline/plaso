# -*- coding: utf-8 -*-
"""Output related functions and classes for testing."""

import unittest

from plaso.formatters import mediator as formatters_mediator
from plaso.output import mediator


class TestConfig(object):
  """Test config value object."""


class OutputModuleTestCase(unittest.TestCase):
  """The unit test case for a output module."""

  # Show full diff results, part of TestCase so does not follow our naming
  # conventions.
  maxDiff = None

  def _CreateOutputMediator(self, config=None, storage_object=None):
    """Creates a test output mediator.

    Args:
      config: optional configuration object, containing config information.
              The default is None.
      storage_object: optional storage file object (instance of StorageFile)
                      that defines the storage. The default is None.

    Returns:
      An output mediator (instance of OutputMediator).
    """
    formatter_mediator = formatters_mediator.FormatterMediator()
    return mediator.OutputMediator(
        formatter_mediator, storage_object, config=config)
