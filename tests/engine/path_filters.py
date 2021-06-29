#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""Tests for the path filter."""

import io
import unittest

from dfvfs.helpers import file_system_searcher
from dfvfs.lib import definitions as dfvfs_definitions
from dfvfs.path import factory as path_spec_factory
from dfvfs.resolver import resolver as path_spec_resolver

from plaso.containers import artifacts
from plaso.engine import filter_file
from plaso.engine import path_filters
from plaso.engine import yaml_filter_file

from tests import test_lib as shared_test_lib


class PathFilterTest(shared_test_lib.BaseTestCase):
  """Tests for the path filter."""

  def testInitialize(self):
    """Tests the __init__ function."""
    test_filter = path_filters.PathFilter(
        path_filters.PathFilter.FILTER_TYPE_INCLUDE)
    self.assertIsNotNone(test_filter)

    with self.assertRaises(ValueError):
      test_filter = path_filters.PathFilter('bogus')


class PathCollectionFiltersHelperTest(shared_test_lib.BaseTestCase):
  """Tests for the path collection filters helper."""

  # pylint: disable=protected-access

  _FILTER_FILE_DATA = '\n'.join([
      '# 2 hits.',
      '/test_data/testdir/filter_.+.txt',
      '# A single hit.',
      '/test_data/.+evtx',
      '# A single hit.',
      '/AUTHORS',
      '/does_not_exist/some_file_[0-9]+txt',
      '# Path expansion.',
      '{systemroot}/Tasks/.+[.]job',
      '# This should not compile properly, missing file information.',
      'failing/',
      '# This should not fail during initial loading, but fail later on.',
      'bad re (no close on that parenthesis/file',
      ''])

  _YAML_FILTER_FILE_DATA = '\n'.join([
      'type: include',
      'paths:',
      '- \'bad re (no close on that parenthesis/file\'',
      '- \'failing/\'',
      '- \'/does_not_exist/some_file_[0-9]+txt\'',
      '---',
      'type: include',
      'path_separator: \'\\\'',
      'paths:',
      '- \'\\\\AUTHORS\'',
      '- \'{systemroot}\\\\Tasks\\\\.+[.]job\'',
      '---',
      'type: include',
      'paths:',
      '- \'/test_data/.+evtx\'',
      '- \'/test_data/testdir/filter_.+.txt\'',
      ''])

  def testBuildFindSpecs(self):
    """Tests the BuildFindSpecs function."""
    test_file_path = self._GetTestFilePath(['System.evtx'])
    self._SkipIfPathNotExists(test_file_path)

    test_file_path = self._GetTestFilePath(['testdir', 'filter_1.txt'])
    self._SkipIfPathNotExists(test_file_path)

    test_file_path = self._GetTestFilePath(['testdir', 'filter_3.txt'])
    self._SkipIfPathNotExists(test_file_path)

    test_filter_file = filter_file.FilterFile()
    test_path_filters = test_filter_file._ReadFromFileObject(
        io.StringIO(self._FILTER_FILE_DATA))

    environment_variable = artifacts.EnvironmentVariableArtifact(
        case_sensitive=False, name='SystemRoot', value='C:\\Windows')

    test_helper = path_filters.PathCollectionFiltersHelper()
    test_helper.BuildFindSpecs(
        test_path_filters, environment_variables=[environment_variable])

    self.assertEqual(len(test_helper.included_file_system_find_specs), 5)

    path_spec = path_spec_factory.Factory.NewPathSpec(
        dfvfs_definitions.TYPE_INDICATOR_OS, location='.')
    file_system = path_spec_resolver.Resolver.OpenFileSystem(path_spec)
    searcher = file_system_searcher.FileSystemSearcher(
        file_system, path_spec)

    path_spec_generator = searcher.Find(
        find_specs=test_helper.included_file_system_find_specs)
    self.assertIsNotNone(path_spec_generator)

    path_specs = list(path_spec_generator)

    # Two evtx, one symbolic link to evtx, one AUTHORS, two filter_*.txt files,
    # total 6 path specifications.
    self.assertEqual(len(path_specs), 6)

  def testBuildFindSpecsWithYAMLFilterFile(self):
    """Tests the BuildFindSpecs function with YAML filter file."""
    test_file_path = self._GetTestFilePath(['System.evtx'])
    self._SkipIfPathNotExists(test_file_path)

    test_file_path = self._GetTestFilePath(['testdir', 'filter_1.txt'])
    self._SkipIfPathNotExists(test_file_path)

    test_file_path = self._GetTestFilePath(['testdir', 'filter_3.txt'])
    self._SkipIfPathNotExists(test_file_path)

    test_filter_file = yaml_filter_file.YAMLFilterFile()
    test_path_filters = test_filter_file._ReadFromFileObject(
        io.StringIO(self._YAML_FILTER_FILE_DATA))

    environment_variable = artifacts.EnvironmentVariableArtifact(
        case_sensitive=False, name='SystemRoot', value='C:\\Windows')

    test_helper = path_filters.PathCollectionFiltersHelper()
    test_helper.BuildFindSpecs(
        test_path_filters, environment_variables=[environment_variable])

    self.assertEqual(len(test_helper.included_file_system_find_specs), 5)

    path_spec = path_spec_factory.Factory.NewPathSpec(
        dfvfs_definitions.TYPE_INDICATOR_OS, location='.')
    file_system = path_spec_resolver.Resolver.OpenFileSystem(path_spec)
    searcher = file_system_searcher.FileSystemSearcher(
        file_system, path_spec)

    path_spec_generator = searcher.Find(
        find_specs=test_helper.included_file_system_find_specs)
    self.assertIsNotNone(path_spec_generator)

    path_specs = list(path_spec_generator)

    # Two evtx, one symbolic link to evtx, one AUTHORS, two filter_*.txt files,
    # total 6 path specifications.
    self.assertEqual(len(path_specs), 6)


if __name__ == '__main__':
  unittest.main()
