# -*- coding: utf-8 -*-
"""Output related functions and classes for testing."""

import shutil
import tempfile
import unittest

from plaso.formatters import mediator as formatters_mediator
from plaso.output import mediator


class TestConfig(object):
  """Test config value object."""


class TempDirectory(object):
  """A self cleaning temporary directory."""

  def __init__(self):
    """Initializes the temporary directory."""
    super(TempDirectory, self).__init__()
    self.name = u''

  def __enter__(self):
    """Make this work with the 'with' statement."""
    self.name = tempfile.mkdtemp()
    return self.name

  def __exit__(self, unused_type, unused_value, unused_traceback):
    """Make this work with the 'with' statement."""
    shutil.rmtree(self.name, True)


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
