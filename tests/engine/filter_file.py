#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""Tests for the filter file."""

from __future__ import unicode_literals

import logging
import os
import tempfile
import unittest

from dfvfs.helpers import file_system_searcher
from dfvfs.lib import definitions as dfvfs_definitions
from dfvfs.path import factory as path_spec_factory
from dfvfs.resolver import resolver as path_spec_resolver

from plaso.containers import artifacts
from plaso.engine import filter_file

from tests import test_lib as shared_test_lib


class FilterFileTestCase(shared_test_lib.BaseTestCase):
  """Tests for the filter file."""

  @shared_test_lib.skipUnlessHasTestFile(['System.evtx'])
  @shared_test_lib.skipUnlessHasTestFile(['testdir', 'filter_1.txt'])
  @shared_test_lib.skipUnlessHasTestFile(['testdir', 'filter_3.txt'])
  def testBuildFindSpecs(self):
    """Tests the BuildFindSpecs function."""
    filter_file_path = ''
    with tempfile.NamedTemporaryFile(delete=False) as temp_file:
      test_filter_file = filter_file.FilterFile(temp_file.name)
      # 2 hits.
      temp_file.write(b'/test_data/testdir/filter_.+.txt\n')
      # A single hit.
      temp_file.write(b'/test_data/.+evtx\n')
      # A single hit.
      temp_file.write(b'/AUTHORS\n')
      temp_file.write(b'/does_not_exist/some_file_[0-9]+txt\n')
      # Path expansion.
      temp_file.write(b'{systemroot}/Tasks/.+[.]job\n')
      # This should not compile properly, missing file information.
      temp_file.write(b'failing/\n')
      # This should not fail during initial loading, but fail later on.
      temp_file.write(b'bad re (no close on that parenthesis/file\n')

    environment_variable = artifacts.EnvironmentVariableArtifact(
        case_sensitive=False, name='SystemRoot', value='C:\\Windows')

    find_specs = test_filter_file.BuildFindSpecs(
        environment_variables=[environment_variable])

    try:
      os.remove(filter_file_path)
    except (OSError, IOError) as exception:
      logging.warning(
          'Unable to remove filter file: {0:s} with error: {1!s}'.format(
              filter_file_path, exception))

    self.assertEqual(len(find_specs), 5)

    path_spec = path_spec_factory.Factory.NewPathSpec(
        dfvfs_definitions.TYPE_INDICATOR_OS, location='.')
    file_system = path_spec_resolver.Resolver.OpenFileSystem(path_spec)
    searcher = file_system_searcher.FileSystemSearcher(
        file_system, path_spec)

    path_spec_generator = searcher.Find(find_specs=find_specs)
    self.assertIsNotNone(path_spec_generator)

    path_specs = list(path_spec_generator)
    # Two evtx, one symbolic link to evtx, one AUTHORS, two filter_*.txt files,
    # total 6 path specifications.
    self.assertEqual(len(path_specs), 6)

    with self.assertRaises(IOError):
      test_filter_file = filter_file.FilterFile('thisfiledoesnotexist')
      test_filter_file.BuildFindSpecs()

    file_system.Close()


if __name__ == '__main__':
  unittest.main()
