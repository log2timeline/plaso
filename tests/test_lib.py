# -*- coding: utf-8 -*-
"""Shared functions and classes for testing."""

from __future__ import unicode_literals

import io
import os
import shutil
import re
import sys
import tempfile
import unittest

from dfvfs.lib import definitions as dfvfs_definitions
from dfvfs.path import factory as path_spec_factory
from dfvfs.resolver import resolver as path_spec_resolver


def skipUnlessHasTestFile(path_segments):  # pylint: disable=invalid-name
  """Decorator to skip a test if the test file does not exist.

  Args:
    path_segments (list[str]): path segments inside the test data directory.

  Returns:
    function: to invoke.
  """
  fail_unless_has_test_file = getattr(
      unittest, 'fail_unless_has_test_file', False)

  path = os.path.join('test_data', *path_segments)
  if fail_unless_has_test_file or os.path.exists(path):
    return lambda function: function

  if sys.version_info[0] < 3:
    path = path.encode('utf-8')

  # Note that the message should be of type str which is different for
  # different versions of Python.
  return unittest.skip('missing test file: {0:s}'.format(path))


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
    """
    path = self._GetTestFilePath(path_segments)
    path_spec = path_spec_factory.Factory.NewPathSpec(
        dfvfs_definitions.TYPE_INDICATOR_OS, location=path)
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

  def _GetTestFilePathSpec(self, path_segments):
    """Retrieves a path specification of a test file in the test data directory.

    Args:
      path_segments (list[str]): components of a path to a test file, relative
          to the test_data directory.

    Returns:
      dfvfs.PathSpec: path specification.
    """
    path = self._GetTestFilePath(path_segments)
    return path_spec_factory.Factory.NewPathSpec(
        dfvfs_definitions.TYPE_INDICATOR_OS, location=path)


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
