# -*- coding: utf-8 -*-
"""CLI related functions and classes for testing."""

import os
import unittest


class CLIToolTestCase(unittest.TestCase):
  """The unit test case for a CLI tool."""

  # Show full diff results, part of TestCase so does not follow our naming
  # conventions.
  maxDiff = None

  _TEST_DATA_PATH = os.path.join(os.getcwd(), u'test_data')

  def _GetTestFilePath(self, path_segments):
    """Retrieves the path of a test file relative to the test data directory.

    Args:
      path_segments: the path segments inside the test data directory.

    Returns:
      A path of the test file.
    """
    # Note that we need to pass the individual path segments to os.path.join
    # and not a list.
    return os.path.join(self._TEST_DATA_PATH, *path_segments)
