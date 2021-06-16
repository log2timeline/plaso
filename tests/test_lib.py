# -*- coding: utf-8 -*-
"""Shared functions and classes for testing."""

import io
import os
import shutil
import re
import tempfile
import unittest

from dfdatetime import time_elements
from dfvfs.lib import definitions as dfvfs_definitions
from dfvfs.path import factory as path_spec_factory
from dfvfs.resolver import resolver as path_spec_resolver


# The path to top of the Plaso source tree.
PROJECT_PATH = os.path.abspath(os.path.join(os.path.dirname(__file__), '..'))
# The paths below are all derived from the project path directory.
# They are enumerated explicitly here so that they can be overwritten for
# compatibility with different build systems.
ANALYSIS_PATH = os.path.join(PROJECT_PATH, 'plaso', 'analysis')
ANALYZERS_PATH = os.path.join(PROJECT_PATH, 'plaso', 'analyzers')
CLI_HELPERS_PATH = os.path.join(PROJECT_PATH, 'plaso', 'cli', 'helpers')
CONTAINERS_PATH = os.path.join(PROJECT_PATH, 'plaso', 'containers')
DATA_PATH = os.path.join(PROJECT_PATH, 'data')
OUTPUT_PATH = os.path.join(PROJECT_PATH, 'plaso', 'output')
PARSERS_PATH = os.path.join(PROJECT_PATH, 'plaso', 'parsers')
PREPROCESSORS_PATH = os.path.join(PROJECT_PATH, 'plaso', 'preprocessors')
TEST_DATA_PATH = os.path.join(PROJECT_PATH, 'test_data')


def GetTestFilePath(path_segments):
  """Retrieves the path of a file in the test data directory.

  Args:
    path_segments (list[str]): path segments inside the test data directory.

  Returns:
    str: path of the test file.
  """
  # Note that we need to pass the individual path segments to os.path.join
  # and not a list.
  return os.path.join(TEST_DATA_PATH, *path_segments)


def CopyTimestampFromString(time_string):
  """Copies a date and time string to a Plaso timestamp.

  Args:
    time_string (str): a date and time string formatted as:
        "YYYY-MM-DD hh:mm:ss.######[+-]##:##", where # are numeric digits
        ranging from 0 to 9 and the seconds fraction can be either 3 or 6
        digits. The time of day, seconds fraction and timezone offset are
        optional. The default timezone is UTC.

  Returns:
    int: timestamp which contains the number of microseconds since January 1,
        1970, 00:00:00 UTC.

  Raises:
    ValueError: if the time string is invalid or not supported.
  """
  date_time = time_elements.TimeElementsInMicroseconds()
  date_time.CopyFromDateTimeString(time_string)

  return date_time.GetPlasoTimestamp()


class BaseTestCase(unittest.TestCase):
  """The base test case."""

  # Show full diff results, part of TestCase so does not follow our naming
  # conventions.
  maxDiff = None

  def _GetDataFilePath(self, path_segments):
    """Retrieves the path of a file in the data directory.

    Args:
      path_segments (list[str]): path segments inside the data directory.

    Returns:
      str: path of the test file.
    """
    # Note that we need to pass the individual path segments to os.path.join
    # and not a list.
    return os.path.join(DATA_PATH, *path_segments)

  def _GetTestFileEntry(self, path_segments):
    """Creates a file entry that references a file in the test data directory.

    Args:
      path_segments (list[str]): path segments inside the test data directory.

    Returns:
      dfvfs.FileEntry: file entry.

    Raises:
      SkipTest: if the path inside the test data directory does not exist and
          the test should be skipped.
    """
    path_spec = self._GetTestFilePathSpec(path_segments)
    return path_spec_resolver.Resolver.OpenFileEntry(path_spec)

  def _GetTestFilePath(self, path_segments):
    """Retrieves the path of a file in the test data directory.

    Args:
      path_segments (list[str]): path segments inside the test data directory.

    Returns:
      str: path of the test file.
    """
    # Note that we need to pass the individual path segments to os.path.join
    # and not a list.
    return os.path.join(TEST_DATA_PATH, *path_segments)

  def _GetTestFilePathSpec(self, path_segments):
    """Retrieves the path specification of a file in the test data directory.

    Args:
      path_segments (list[str]): path segments inside the test data directory.

    Returns:
      dfvfs.PathSpec: path specification.

    Raises:
      SkipTest: if the path does not exist and the test should be skipped.
    """
    test_file_path = self._GetTestFilePath(path_segments)
    self._SkipIfPathNotExists(test_file_path)

    return path_spec_factory.Factory.NewPathSpec(
        dfvfs_definitions.TYPE_INDICATOR_OS, location=test_file_path)

  def _SkipIfPathNotExists(self, path):
    """Skips the test if the path does not exist.

    Args:
      path (str): path of a test file.

    Raises:
      SkipTest: if the path does not exist and the test should be skipped.
    """
    if not os.path.exists(path):
      filename = os.path.basename(path)
      raise unittest.SkipTest('missing test file: {0:s}'.format(filename))


class ImportCheckTestCase(BaseTestCase):
  """Base class for tests that check modules are imported correctly."""

  _FILENAME_REGEXP = re.compile(r'^[^_].*\.py$')

  def _AssertFilesImportedInInit(self, path, ignorable_files):
    """Checks that files in path are imported in __init__.py

    Args:
      path (str): path to directory containing an __init__.py file and other
          Python files which should be imported.
      ignorable_files (list[str]): names of Python files that don't need to
          appear in __init__.py. For example, 'manager.py'.
    """
    init_path = '{0:s}/__init__.py'.format(path)
    with io.open(init_path, mode='r', encoding='utf-8') as init_file:
      init_content = init_file.read()

    for file_path in os.listdir(path):
      filename = os.path.basename(file_path)
      if filename in ignorable_files:
        continue
      if self._FILENAME_REGEXP.search(filename):
        module_name, _, _ = filename.partition('.')
        import_expression = re.compile(r' import {0:s}\b'.format(module_name))

        self.assertRegex(
            init_content, import_expression,
            '{0:s} not imported in {1:s}'.format(module_name, init_path))


class TempDirectory(object):
  """Class that implements a temporary directory."""

  def __init__(self):
    """Initializes a temporary directory."""
    super(TempDirectory, self).__init__()
    self.name = ''

  def __enter__(self):
    """Make this work with the 'with' statement."""
    self.name = tempfile.mkdtemp()
    return self.name

  def __exit__(self, exception_type, value, traceback):
    """Make this work with the 'with' statement."""
    shutil.rmtree(self.name, True)
