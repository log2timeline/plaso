# -*- coding: utf-8 -*-
"""CLI related functions and classes for testing."""

import io
import shutil
import tempfile
import os
import unittest

from plaso.cli import tools


class TempDirectory(object):
  """Class that implements a temporar directory."""

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


class TestOutputWriter(tools.FileObjectOutputWriter):
  """Class that implements a test output writer."""

  def __init__(self, encoding=u'utf-8'):
    """Initializes the output writer object.

    Args:
      encoding: optional output encoding. The default is "utf-8".
    """
    file_object = io.BytesIO()
    super(TestOutputWriter, self).__init__(file_object, encoding=encoding)
    self._read_offset = 0

  def ReadOutput(self):
    """Reads the newly added output data.

    Returns:
      A binary string of the encoded output data.
    """
    self._file_object.seek(self._read_offset, os.SEEK_SET)
    output_data = self._file_object.read()
    self._read_offset = self._file_object.tell()

    return output_data


class TestOptions(object):
  """Class to define test options."""


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
