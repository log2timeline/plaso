# -*- coding: utf-8 -*-
"""Analyzer related functions and classes for testing."""

from dfvfs.lib import definitions as dfvfs_definitions
from dfvfs.path import factory as path_spec_factory
from dfvfs.resolver import resolver as path_spec_resolver

from tests import test_lib as shared_test_lib


class AnalyzerTestCase(shared_test_lib.BaseTestCase):
  """Parent test case for a analyzer."""

  def _GetTestFileEntry(self, path_segments):
    """Creates a file entry that references a file in the test data directory.

    Args:
      path_segments (list[str]): components of a path to a test file, relative
          to the test_data directory.

    Returns:
      dfvfs.FileEntry: file entry.
    """
    path = self._GetTestFilePath(path_segments)
    path_spec = path_spec_factory.Factory.NewPathSpec(
        dfvfs_definitions.TYPE_INDICATOR_OS, location=path)
    return path_spec_resolver.Resolver.OpenFileEntry(path_spec)
