# -*- coding: utf-8 -*-
"""Shared functions and classes for testing."""

from __future__ import unicode_literals

import io
import os
import shutil
import re
import tempfile
import unittest

from dfvfs.lib import definitions as dfvfs_definitions
from dfvfs.path import factory as path_spec_factory
from dfvfs.resolver import resolver as path_spec_resolver


def GetTestFilePath(path_segments):
  """Retrieves the path of a test file in the test data directory.

  Args:
    path_segments (list[str]): path segments inside the test data directory.

  Returns:
    str: path of the test file.
  """
  # Note that we need to pass the individual path segments to os.path.join
  # and not a list.
  return os.path.join(os.getcwd(), 'test_data', *path_segments)


class BaseTestCase(unittest.TestCase):
  """The base test case."""

  _DATA_PATH = os.path.join(os.getcwd(), 'data')
  _TEST_DATA_PATH = os.path.join(os.getcwd(), 'test_data')

  # Show full diff results, part of TestCase so does not follow our naming
  # conventions.
  maxDiff = None

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
    test_file_path = self._GetTestFilePath(path_segments)
    self._SkipIfPathNotExists(test_file_path)

    path_spec = path_spec_factory.Factory.NewPathSpec(
        dfvfs_definitions.TYPE_INDICATOR_OS, location=test_file_path)
    return path_spec_resolver.Resolver.OpenFileEntry(path_spec)

  def _GetTestFilePath(self, path_segments):
    """Retrieves the path of a test file in the test data directory.

    Args:
      path_segments (list[str]): path segments inside the test data directory.

    Returns:
      str: path of the test file.
    """
    # Note that we need to pass the individual path segments to os.path.join
    # and not a list.
    return os.path.join(self._TEST_DATA_PATH, *path_segments)

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

        # pylint: disable=deprecated-method
        # TODO: replace by assertRegex once Python 2 support is removed.
        self.assertRegexpMatches(
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
