#!/usr/bin/python
# -*- coding: utf-8 -*-
"""Tests for the extractor classes."""

import os
import shutil
import unittest

from dfvfs.helpers import file_system_searcher
from dfvfs.lib import definitions as dfvfs_definitions
from dfvfs.path import factory as path_spec_factory
from dfvfs.resolver import context

from plaso.engine import extractors

from tests import test_lib as shared_test_lib


# TODO: add EventExtractorTest


class PathSpecExtractorTest(shared_test_lib.BaseTestCase):
  """Tests for the path specification extractor."""

  def _GetFilePaths(self, path_specs):
    """Retrieves file paths from path specifications.

    Args:
      path_specs (list[dfvfs.PathSpec]): path specifications.

    Returns:
      list[str]: file paths.
    """
    file_paths = []
    for path_spec in path_specs:
      data_stream = getattr(path_spec, u'data_stream', None)
      location = getattr(path_spec, u'location', None)
      if location is not None:
        if data_stream:
          location = u'{0:s}:{1:s}'.format(location, data_stream)
        file_paths.append(location)

    return file_paths

  def _GetFindSpecs(self, location_expressions):
    """Retrieves find specifications from location expressions.

    Args:
      location_expressions (list[str]): location regular expressions.

    Returns:
      list[dfvfs.FindSpec]: find specifications for the file system searcher.
    """
    find_specs = []
    for location_expression in location_expressions:
      # Convert the filter paths into a list of path segments and strip
      # the root path segment.
      path_segments = location_expression.split(u'/')
      path_segments.pop(0)

      find_spec = file_system_searcher.FindSpec(
          location_regex=path_segments, case_sensitive=False)
      find_specs.append(find_spec)

    return find_specs

  @shared_test_lib.skipUnlessHasTestFile([u'syslog.bz2'])
  @shared_test_lib.skipUnlessHasTestFile([u'syslog.tgz'])
  @shared_test_lib.skipUnlessHasTestFile([u'syslog.zip'])
  @shared_test_lib.skipUnlessHasTestFile([u'wtmp.1'])
  def testExtractPathSpecsFileSystem(self):
    """Tests the ExtractPathSpecs function on the file system."""
    test_files = [
        self._GetTestFilePath([u'syslog.bz2']),
        self._GetTestFilePath([u'syslog.tgz']),
        self._GetTestFilePath([u'syslog.zip']),
        self._GetTestFilePath([u'wtmp.1'])]

    with shared_test_lib.TempDirectory() as temp_directory:
      for a_file in test_files:
        shutil.copy(a_file, temp_directory)

      source_path_spec = path_spec_factory.Factory.NewPathSpec(
          dfvfs_definitions.TYPE_INDICATOR_OS, location=temp_directory)

      resolver_context = context.Context()
      test_extractor = extractors.PathSpecExtractor()
      path_specs = list(test_extractor.ExtractPathSpecs(
          [source_path_spec], resolver_context=resolver_context))

      self.assertEqual(len(path_specs), 4)

  @shared_test_lib.skipUnlessHasTestFile([u'System.evtx'])
  @shared_test_lib.skipUnlessHasTestFile([u'testdir', u'filter_1.txt'])
  @shared_test_lib.skipUnlessHasTestFile([u'testdir', u'filter_3.txt'])
  def testExtractPathSpecsFileSystemWithFindSpecs(self):
    """Tests the ExtractPathSpecs function with find specifications."""
    location_expressions = [
        u'/test_data/testdir/filter_.+.txt',
        u'/test_data/.+evtx',
        u'/AUTHORS',
        u'/does_not_exist/some_file_[0-9]+txt']

    source_path_spec = path_spec_factory.Factory.NewPathSpec(
        dfvfs_definitions.TYPE_INDICATOR_OS, location=u'.')

    resolver_context = context.Context()
    test_extractor = extractors.PathSpecExtractor()

    find_specs = self._GetFindSpecs(location_expressions)
    path_specs = list(test_extractor.ExtractPathSpecs(
        [source_path_spec], find_specs=find_specs,
        resolver_context=resolver_context))

    # Two files with test_data/testdir/filter_*.txt, AUTHORS
    # and test_data/System.evtx and test_data/System2.evtx.
    self.assertEqual(len(path_specs), 5)

    paths = self._GetFilePaths(path_specs)

    current_directory = os.getcwd()

    expected_path = os.path.join(
        current_directory, u'test_data', u'testdir', u'filter_1.txt')
    self.assertTrue(expected_path in paths)

    expected_path = os.path.join(
        current_directory, u'test_data', u'testdir', u'filter_2.txt')
    self.assertFalse(expected_path in paths)

    expected_path = os.path.join(
        current_directory, u'test_data', u'testdir', u'filter_3.txt')
    self.assertTrue(expected_path in paths)

    expected_path = os.path.join(
        current_directory, u'AUTHORS')
    self.assertTrue(expected_path in paths)

  @shared_test_lib.skipUnlessHasTestFile([u'syslog_image.dd'])
  def testExtractPathSpecsStorageMediaImage(self):
    """Tests the ExtractPathSpecs function an image file.

    The image file contains the following files:
    * logs/hidden.zip
    * logs/sys.tgz

    The hidden.zip file contains one file, syslog, which is the
    same for sys.tgz.

    The end results should therefore be:
    * logs/hidden.zip (unchanged)
    * logs/hidden.zip:syslog (the text file extracted out)
    * logs/sys.tgz (unchanged)
    * logs/sys.tgz (read as a GZIP file, so not compressed)
    * logs/sys.tgz:syslog.gz (A GZIP file from the TAR container)
    * logs/sys.tgz:syslog.gz:syslog (the extracted syslog file)

    This means that the collection script should collect 6 files in total.
    """
    test_file = self._GetTestFilePath([u'syslog_image.dd'])

    volume_path_spec = path_spec_factory.Factory.NewPathSpec(
        dfvfs_definitions.TYPE_INDICATOR_OS, location=test_file)
    source_path_spec = path_spec_factory.Factory.NewPathSpec(
        dfvfs_definitions.TYPE_INDICATOR_TSK, location=u'/',
        parent=volume_path_spec)

    resolver_context = context.Context()
    test_extractor = extractors.PathSpecExtractor()
    path_specs = list(test_extractor.ExtractPathSpecs(
        [source_path_spec], resolver_context=resolver_context))

    self.assertEqual(len(path_specs), 3)

  @shared_test_lib.skipUnlessHasTestFile([u'ímynd.dd'])
  def testExtractPathSpecsStorageMediaImageWithFilter(self):
    """Tests the ExtractPathSpecs function on an image file with a filter."""
    location_expressions = [
        u'/a_directory/.+zip',
        u'/a_directory/another.+',
        u'/passwords.txt']

    test_file = self._GetTestFilePath([u'ímynd.dd'])

    volume_path_spec = path_spec_factory.Factory.NewPathSpec(
        dfvfs_definitions.TYPE_INDICATOR_OS, location=test_file)
    source_path_spec = path_spec_factory.Factory.NewPathSpec(
        dfvfs_definitions.TYPE_INDICATOR_TSK, location=u'/',
        parent=volume_path_spec)

    resolver_context = context.Context()
    test_extractor = extractors.PathSpecExtractor()

    find_specs = self._GetFindSpecs(location_expressions)
    path_specs = list(test_extractor.ExtractPathSpecs(
        [source_path_spec], find_specs=find_specs,
        resolver_context=resolver_context))

    self.assertEqual(len(path_specs), 2)

    paths = self._GetFilePaths(path_specs)

    # path_specs[0]
    # type: TSK
    # file_path: '/a_directory/another_file'
    # container_path: 'test_data/ímynd.dd'
    # image_offset: 0
    self.assertEqual(paths[0], u'/a_directory/another_file')

    # path_specs[1]
    # type: TSK
    # file_path: '/passwords.txt'
    # container_path: 'test_data/ímynd.dd'
    # image_offset: 0
    self.assertEqual(paths[1], u'/passwords.txt')

  @shared_test_lib.skipUnlessHasTestFile([u'multi_partition_image.vmdk'])
  def testExtractPathSpecsStorageMediaImageWithPartitions(self):
    """Tests the ExtractPathSpecs function an image file with partitions.

    The image file contains 2 partitions, p1 and p2, both with a NFTS
    file systems.
    """
    # Note that the source file is a RAW (VMDK flat) image.
    test_file = self._GetTestFilePath([u'multi_partition_image.vmdk'])

    image_path_spec = path_spec_factory.Factory.NewPathSpec(
        dfvfs_definitions.TYPE_INDICATOR_OS, location=test_file)

    p1_path_spec = path_spec_factory.Factory.NewPathSpec(
        dfvfs_definitions.TYPE_INDICATOR_TSK_PARTITION, location=u'/p1',
        part_index=2, start_offset=0x00010000, parent=image_path_spec)
    p1_file_system_path_spec = path_spec_factory.Factory.NewPathSpec(
        dfvfs_definitions.TYPE_INDICATOR_TSK, location=u'/',
        parent=p1_path_spec)

    p2_path_spec = path_spec_factory.Factory.NewPathSpec(
        dfvfs_definitions.TYPE_INDICATOR_TSK_PARTITION, location=u'/p2',
        part_index=3, start_offset=0x00510000, parent=image_path_spec)
    p2_file_system_path_spec = path_spec_factory.Factory.NewPathSpec(
        dfvfs_definitions.TYPE_INDICATOR_TSK, location=u'/',
        parent=p2_path_spec)

    resolver_context = context.Context()
    test_extractor = extractors.PathSpecExtractor(resolver_context)

    path_specs = list(test_extractor.ExtractPathSpecs(
        [p1_file_system_path_spec, p2_file_system_path_spec],
        resolver_context=resolver_context))

    expected_paths_p1 = [
        u'/$AttrDef',
        u'/$BadClus',
        u'/$BadClus:$Bad',
        u'/$Bitmap',
        u'/$Boot',
        u'/$Extend',
        u'/$Extend/$ObjId',
        u'/$Extend/$Quota',
        u'/$Extend/$Reparse',
        u'/$Extend/$RmMetadata',
        u'/$Extend/$RmMetadata/$Repair',
        u'/$Extend/$RmMetadata/$Repair:$Config',
        u'/$Extend/$RmMetadata/$TxfLog',
        u'/$LogFile',
        u'/$MFT',
        u'/$MFTMirr',
        u'/$Secure',
        u'/$Secure:$SDS',
        u'/$UpCase',
        u'/$Volume',
        u'/file1.txt',
        u'/file2.txt']

    expected_paths_p2 = [
        u'/$AttrDef',
        u'/$BadClus',
        u'/$BadClus:$Bad',
        u'/$Bitmap',
        u'/$Boot',
        u'/$Extend',
        u'/$Extend/$ObjId',
        u'/$Extend/$Quota',
        u'/$Extend/$Reparse',
        u'/$Extend/$RmMetadata',
        u'/$Extend/$RmMetadata/$Repair',
        u'/$Extend/$RmMetadata/$Repair:$Config',
        u'/$Extend/$RmMetadata/$TxfLog',
        u'/$LogFile',
        u'/$MFT',
        u'/$MFTMirr',
        u'/$Secure',
        u'/$Secure:$SDS',
        u'/$UpCase',
        u'/$Volume',
        u'/file1_on_part_2.txt',
        u'/file2_on_part_2.txt']

    paths = self._GetFilePaths(path_specs)
    expected_paths = expected_paths_p1
    expected_paths.extend(expected_paths_p2)

    self.assertEqual(len(path_specs), len(expected_paths))
    self.assertEqual(sorted(paths), sorted(expected_paths))


if __name__ == '__main__':
  unittest.main()
