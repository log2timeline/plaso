# -*- coding: utf-8 -*-
"""Front-end related functions and classes for testing."""

import io
import os
import shutil
import tempfile
import unittest


class StringIOOutputWriter(object):
  """Class that implements a StringIO output writer."""

  def __init__(self):
    """Initialize the string output writer."""
    super(StringIOOutputWriter, self).__init__()
    self._string_io = io.StringIO()

    # Make the output writer compatible with a filehandle interface.
    self.write = self.Write

  def flush(self):
    """Flush the internal buffer."""
    self._string_io.flush()

  def GetValue(self):
    """Returns the write buffer from the output writer."""
    return self._string_io.getvalue()

  def GetLine(self):
    """Returns a single line read from the output buffer."""
    return self._string_io.readline()

  def SeekToBeginning(self):
    """Seeks the output buffer to the beginning of the buffer."""
    self._string_io.seek(0)

  def Write(self, string):
    """Writes a string to the StringIO object."""
    self._string_io.write(string)


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


class FrontendTestCase(unittest.TestCase):
  """The unit test case for a front-end."""

  _DATA_PATH = os.path.join(os.getcwd(), u'data')
  _TEST_DATA_PATH = os.path.join(os.getcwd(), u'test_data')

  # Show full diff results, part of TestCase so does not follow our naming
  # conventions.
  maxDiff = None

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
