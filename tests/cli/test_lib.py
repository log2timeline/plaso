# -*- coding: utf-8 -*-
"""CLI related functions and classes for testing."""

import io
import os
import unittest

from plaso.cli import tools


class TestOutputWriter(tools.FileObjectOutputWriter):
  """Class that implements a test output writer."""

  def __init__(self, encoding=u'utf-8'):
    """Initializes the output writer object.

    Args:
      encoding: optional output encoding.
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

  def _RunArgparseFormatHelp(self, argument_parser):
    """Runs argparse.format_help() with test conditions.

    Args:
      argument_parser: an argument parser object (instance of
                       argparse.ArgumentParser).

    Returns:
      A binary string containing the output of argparse.format_help().
    """
    columns_environment_variable = os.environ.get(u'COLUMNS', None)
    os.environ[u'COLUMNS'] = u'80'

    try:
      output = argument_parser.format_help()
    finally:
      if columns_environment_variable:
        os.environ[u'COLUMNS'] = columns_environment_variable
      else:
        del os.environ[u'COLUMNS']

    return output
