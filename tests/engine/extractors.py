#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""Tests for the extractor classes."""

from __future__ import unicode_literals

import os
import shutil
import unittest

from dfvfs.helpers import file_system_searcher
from dfvfs.lib import definitions as dfvfs_definitions
from dfvfs.path import factory as path_spec_factory
from dfvfs.resolver import context
from dfvfs.resolver import resolver as path_spec_resolver

from plaso.engine import extractors

from tests import test_lib as shared_test_lib


class EventExtractorTest(shared_test_lib.BaseTestCase):
  """Tests for the event extractor."""

  # TODO: add test for _CheckParserCanProcessFileEntry
  # TODO: add test for _GetSignatureMatchParserNames
  # TODO: add test for _InitializeParserObjects
  # TODO: add test for _ParseDataStreamWithParser
  # TODO: add test for _ParseFileEntryWithParser
  # TODO: add test for _ParseFileEntryWithParsers
  # TODO: add test for ParseDataStream
  # TODO: add test for ParseFileEntryMetadata
  # TODO: add test for ParseMetadataFile


class PathSpecExtractorTest(shared_test_lib.BaseTestCase):
  """Tests for the path specification extractor."""

  # pylint: disable=protected-access

  def _GetFilePaths(self, path_specs):
    """Retrieves file paths from path specifications.

    Args:
      path_specs (list[dfvfs.PathSpec]): path specifications.

    Returns:
      list[str]: file paths.
    """
    file_paths = []
    for path_spec in path_specs:
      data_stream = getattr(path_spec, 'data_stream', None)
      location = getattr(path_spec, 'location', None)
      if location is not None:
        if data_stream:
          location = '{0:s}:{1:s}'.format(location, data_stream)
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
      find_spec = file_system_searcher.FindSpec(
          case_sensitive=False, location_regex=location_expression,
          location_separator='/')
      find_specs.append(find_spec)

    return find_specs

  def testCalculateNTFSTimeHash(self):
    """Tests the _CalculateNTFSTimeHash function."""
    # Note that the source file is a RAW (VMDK flat) image.
    test_file_path = self._GetTestFilePath(['multi_partition_image.vmdk'])
    self._SkipIfPathNotExists(test_file_path)

    image_path_spec = path_spec_factory.Factory.NewPathSpec(
        dfvfs_definitions.TYPE_INDICATOR_OS, location=test_file_path)

    p1_path_spec = path_spec_factory.Factory.NewPathSpec(
        dfvfs_definitions.TYPE_INDICATOR_TSK_PARTITION, location='/p1',
        part_index=2, start_offset=0x00010000, parent=image_path_spec)
    p1_file_system_path_spec = path_spec_factory.Factory.NewPathSpec(
        dfvfs_definitions.TYPE_INDICATOR_TSK, location='/file1.txt',
        parent=p1_path_spec)

    file_entry = path_spec_resolver.Resolver.OpenFileEntry(
        p1_file_system_path_spec)

    test_extractor = extractors.PathSpecExtractor()
    hash_value = test_extractor._CalculateNTFSTimeHash(file_entry)
    self.assertEqual(hash_value, '6b181becbc9529b73cf3dc35c99a61e7')

    p2_path_spec = path_spec_factory.Factory.NewPathSpec(
        dfvfs_definitions.TYPE_INDICATOR_TSK_PARTITION, location='/p2',
        part_index=3, start_offset=0x00510000, parent=image_path_spec)
    p2_file_system_path_spec = path_spec_factory.Factory.NewPathSpec(
        dfvfs_definitions.TYPE_INDICATOR_TSK, location='/file2_on_part_2.txt',
        parent=p2_path_spec)

    file_entry = path_spec_resolver.Resolver.OpenFileEntry(
        p2_file_system_path_spec)

    test_extractor = extractors.PathSpecExtractor()
    hash_value = test_extractor._CalculateNTFSTimeHash(file_entry)
    self.assertEqual(hash_value, '8738ed1e707fec64cd1593fd81eb26d2')

  # TODO: add test for _ExtractPathSpecs
  # TODO: add test for _ExtractPathSpecsFromDirectory
  # TODO: add test for _ExtractPathSpecsFromFile
  # TODO: add test for _ExtractPathSpecsFromFileSystem

  def testExtractPathSpecsFileSystem(self):
    """Tests the ExtractPathSpecs function on the file system."""
    test_file_paths = []

    test_file_path = self._GetTestFilePath(['syslog.bz2'])
    self._SkipIfPathNotExists(test_file_path)
    test_file_paths.append(test_file_path)

    test_file_path = self._GetTestFilePath(['syslog.tgz'])
    self._SkipIfPathNotExists(test_file_path)
    test_file_paths.append(test_file_path)

    test_file_path = self._GetTestFilePath(['syslog.zip'])
    self._SkipIfPathNotExists(test_file_path)
    test_file_paths.append(test_file_path)

    test_file_path = self._GetTestFilePath(['wtmp.1'])
    self._SkipIfPathNotExists(test_file_path)
    test_file_paths.append(test_file_path)

    with shared_test_lib.TempDirectory() as temp_directory:
      for a_file in test_file_paths:
        shutil.copy(a_file, temp_directory)

      source_path_spec = path_spec_factory.Factory.NewPathSpec(
          dfvfs_definitions.TYPE_INDICATOR_OS, location=temp_directory)

      resolver_context = context.Context()
      test_extractor = extractors.PathSpecExtractor()
      path_specs = list(test_extractor.ExtractPathSpecs(
          [source_path_spec], resolver_context=resolver_context))

      self.assertEqual(len(path_specs), 4)

  def testExtractPathSpecsFileSystemWithFindSpecs(self):
    """Tests the ExtractPathSpecs function with find specifications."""
    test_file_path = self._GetTestFilePath(['System.evtx'])
    self._SkipIfPathNotExists(test_file_path)

    test_file_path = self._GetTestFilePath(['testdir', 'filter_1.txt'])
    self._SkipIfPathNotExists(test_file_path)

    test_file_path = self._GetTestFilePath(['testdir', 'filter_3.txt'])
    self._SkipIfPathNotExists(test_file_path)

    location_expressions = [
        '/test_data/testdir/filter_.+.txt',
        '/test_data/.+evtx',
        '/AUTHORS',
        '/does_not_exist/some_file_[0-9]+txt']

    source_path_spec = path_spec_factory.Factory.NewPathSpec(
        dfvfs_definitions.TYPE_INDICATOR_OS, location='.')

    resolver_context = context.Context()
    test_extractor = extractors.PathSpecExtractor()

    find_specs = self._GetFindSpecs(location_expressions)
    path_specs = list(test_extractor.ExtractPathSpecs(
        [source_path_spec], find_specs=find_specs,
        resolver_context=resolver_context))

    # Two files with test_data/testdir/filter_*.txt, AUTHORS,
    # test_data/System.evtx and test_data/System2.evtx and
    # a symbolic link test_data/link_to_System.evtx.
    self.assertEqual(len(path_specs), 6)

    paths = self._GetFilePaths(path_specs)

    current_directory = os.getcwd()

    expected_path = os.path.join(
        current_directory, 'test_data', 'testdir', 'filter_1.txt')
    self.assertTrue(expected_path in paths)

    expected_path = os.path.join(
        current_directory, 'test_data', 'testdir', 'filter_2.txt')
    self.assertFalse(expected_path in paths)

    expected_path = os.path.join(
        current_directory, 'test_data', 'testdir', 'filter_3.txt')
    self.assertTrue(expected_path in paths)

    expected_path = os.path.join(current_directory, 'AUTHORS')
    self.assertTrue(expected_path in paths)

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
    test_file_path = self._GetTestFilePath(['syslog_image.dd'])
    self._SkipIfPathNotExists(test_file_path)

    volume_path_spec = path_spec_factory.Factory.NewPathSpec(
        dfvfs_definitions.TYPE_INDICATOR_OS, location=test_file_path)
    source_path_spec = path_spec_factory.Factory.NewPathSpec(
        dfvfs_definitions.TYPE_INDICATOR_TSK, location='/',
        parent=volume_path_spec)

    resolver_context = context.Context()
    test_extractor = extractors.PathSpecExtractor()
    path_specs = list(test_extractor.ExtractPathSpecs(
        [source_path_spec], resolver_context=resolver_context))

    self.assertEqual(len(path_specs), 3)

  def testExtractPathSpecsStorageMediaImageWithFilter(self):
    """Tests the ExtractPathSpecs function on an image file with a filter."""
    location_expressions = [
        '/a_directory/.+zip',
        '/a_directory/another.+',
        '/passwords.txt']

    test_file_path = self._GetTestFilePath(['ímynd.dd'])
    self._SkipIfPathNotExists(test_file_path)

    volume_path_spec = path_spec_factory.Factory.NewPathSpec(
        dfvfs_definitions.TYPE_INDICATOR_OS, location=test_file_path)
    source_path_spec = path_spec_factory.Factory.NewPathSpec(
        dfvfs_definitions.TYPE_INDICATOR_TSK, location='/',
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
    # path_spec_type: TSK
    # file_path: '/a_directory/another_file'
    # container_path: 'test_data/ímynd.dd'
    # image_offset: 0
    self.assertEqual(paths[0], '/a_directory/another_file')

    # path_specs[1]
    # path_spec_type: TSK
    # file_path: '/passwords.txt'
    # container_path: 'test_data/ímynd.dd'
    # image_offset: 0
    self.assertEqual(paths[1], '/passwords.txt')

  def testExtractPathSpecsStorageMediaImageWithPartitions(self):
    """Tests the ExtractPathSpecs function an image file with partitions.

    The image file contains 2 partitions, p1 and p2, both with a NFTS
    file systems.
    """
    # Note that the source file is a RAW (VMDK flat) image.
    test_file_path = self._GetTestFilePath(['multi_partition_image.vmdk'])
    self._SkipIfPathNotExists(test_file_path)

    image_path_spec = path_spec_factory.Factory.NewPathSpec(
        dfvfs_definitions.TYPE_INDICATOR_OS, location=test_file_path)

    p1_path_spec = path_spec_factory.Factory.NewPathSpec(
        dfvfs_definitions.TYPE_INDICATOR_TSK_PARTITION, location='/p1',
        part_index=2, start_offset=0x00010000, parent=image_path_spec)
    p1_file_system_path_spec = path_spec_factory.Factory.NewPathSpec(
        dfvfs_definitions.TYPE_INDICATOR_TSK, location='/',
        parent=p1_path_spec)

    p2_path_spec = path_spec_factory.Factory.NewPathSpec(
        dfvfs_definitions.TYPE_INDICATOR_TSK_PARTITION, location='/p2',
        part_index=3, start_offset=0x00510000, parent=image_path_spec)
    p2_file_system_path_spec = path_spec_factory.Factory.NewPathSpec(
        dfvfs_definitions.TYPE_INDICATOR_TSK, location='/',
        parent=p2_path_spec)

    resolver_context = context.Context()
    test_extractor = extractors.PathSpecExtractor(resolver_context)

    path_specs = list(test_extractor.ExtractPathSpecs(
        [p1_file_system_path_spec, p2_file_system_path_spec],
        resolver_context=resolver_context))

    expected_paths_p1 = [
        '/$AttrDef',
        '/$BadClus',
        '/$BadClus:$Bad',
        '/$Bitmap',
        '/$Boot',
        '/$Extend',
        '/$Extend/$ObjId',
        '/$Extend/$Quota',
        '/$Extend/$Reparse',
        '/$Extend/$RmMetadata',
        '/$Extend/$RmMetadata/$Repair',
        '/$Extend/$RmMetadata/$Repair:$Config',
        '/$Extend/$RmMetadata/$TxfLog',
        '/$LogFile',
        '/$MFT',
        '/$MFTMirr',
        '/$Secure',
        '/$Secure:$SDS',
        '/$UpCase',
        '/$Volume',
        '/file1.txt',
        '/file2.txt']

    expected_paths_p2 = [
        '/$AttrDef',
        '/$BadClus',
        '/$BadClus:$Bad',
        '/$Bitmap',
        '/$Boot',
        '/$Extend',
        '/$Extend/$ObjId',
        '/$Extend/$Quota',
        '/$Extend/$Reparse',
        '/$Extend/$RmMetadata',
        '/$Extend/$RmMetadata/$Repair',
        '/$Extend/$RmMetadata/$Repair:$Config',
        '/$Extend/$RmMetadata/$TxfLog',
        '/$LogFile',
        '/$MFT',
        '/$MFTMirr',
        '/$Secure',
        '/$Secure:$SDS',
        '/$UpCase',
        '/$Volume',
        '/file1_on_part_2.txt',
        '/file2_on_part_2.txt']

    paths = self._GetFilePaths(path_specs)
    expected_paths = expected_paths_p1
    expected_paths.extend(expected_paths_p2)

    self.assertEqual(len(path_specs), len(expected_paths))
    self.assertEqual(sorted(paths), sorted(expected_paths))


if __name__ == '__main__':
  unittest.main()
