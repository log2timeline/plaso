# -*- coding: utf-8 -*-
"""Shared functions and classes for testing."""

import os
import shutil
import tempfile
import unittest


class BaseTestCase(unittest.TestCase):
  """The base test case."""

  _DATA_PATH = os.path.join(os.getcwd(), u'data')
  _TEST_DATA_PATH = os.path.join(os.getcwd(), u'test_data')

  # Show full diff results, part of TestCase so does not follow our naming
  # conventions.
  maxDiff = None

  def _GetTestFilePath(self, path_segments):
    """Retrieves a path of a test file in the test data directory.

    Args:
      path_segments: a list of strings containinge the path segments inside
                     the test data directory.

    Returns:
      A path of the test file.
    """
    # Note that we need to pass the individual path segments to os.path.join
    # and not a list.
    return os.path.join(self._TEST_DATA_PATH, *path_segments)


class TempDirectory(object):
  """Class that implements a temporary directory."""

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
