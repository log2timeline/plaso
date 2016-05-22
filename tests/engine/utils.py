#!/usr/bin/python
# -*- coding: utf-8 -*-
"""Tests for the util functions."""

import logging
import os
import tempfile
import unittest

from dfvfs.helpers import file_system_searcher
from dfvfs.lib import definitions as dfvfs_definitions
from dfvfs.path import factory as path_spec_factory
from dfvfs.resolver import resolver as path_spec_resolver

from plaso.engine import utils

from tests import test_lib as shared_test_lib


class BuildFindSpecsFromFileTest(shared_test_lib.BaseTestCase):
  """Tests for the BuildFindSpecsFromFile function."""

  def testBuildFindSpecsFromFile(self):
    """Tests the BuildFindSpecsFromFile function."""
    filter_name = ''
    with tempfile.NamedTemporaryFile(delete=False) as temp_file:
      filter_name = temp_file.name
      # 2 hits.
      temp_file.write('/test_data/testdir/filter_.+.txt\n')
      # A single hit.
      temp_file.write('/test_data/.+evtx\n')
      # A single hit.
      temp_file.write('/AUTHORS\n')
      temp_file.write('/does_not_exist/some_file_[0-9]+txt\n')
      # This should not compile properly, missing file information.
      temp_file.write('failing/\n')
      # This should not fail during initial loading, but fail later on.
      temp_file.write('bad re (no close on that parenthesis/file\n')

    find_specs = utils.BuildFindSpecsFromFile(filter_name)

    try:
      os.remove(filter_name)
    except (OSError, IOError) as exception:
      logging.warning(
          u'Unable to remove temporary file: {0:s} with error: {1:s}'.format(
              filter_name, exception))

    self.assertEqual(len(find_specs), 4)

    path_spec = path_spec_factory.Factory.NewPathSpec(
        dfvfs_definitions.TYPE_INDICATOR_OS, location=u'.')
    file_system = path_spec_resolver.Resolver.OpenFileSystem(path_spec)
    searcher = file_system_searcher.FileSystemSearcher(
        file_system, path_spec)

    path_spec_generator = searcher.Find(find_specs=find_specs)
    self.assertIsNotNone(path_spec_generator)

    path_specs = list(path_spec_generator)
    # One evtx, one AUTHORS, two filter_*.txt files, total 4 files.
    self.assertEqual(len(path_specs), 4)

    with self.assertRaises(IOError):
      _ = utils.BuildFindSpecsFromFile('thisfiledoesnotexist')

    file_system.Close()


if __name__ == '__main__':
  unittest.main()
