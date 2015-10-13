#!/usr/bin/python
# -*- coding: utf-8 -*-
"""Tests for the extraction front-end object."""

import os
import shutil
import tempfile
import unittest

from dfvfs.helpers import source_scanner
from dfvfs.lib import definitions as dfvfs_definitions
from dfvfs.path import factory as path_spec_factory

from plaso.frontend import extraction_frontend
from plaso.lib import pfilter
from plaso.storage import zip_file as storage_zip_file

from tests.frontend import test_lib


class ExtractionFrontendTests(test_lib.FrontendTestCase):
  """Tests for the extraction front-end object."""

  def setUp(self):
    """Sets up the objects used throughout the test."""
    # This is necessary since TimeRangeCache uses class members.
    # TODO: remove this work around and properly fix TimeRangeCache.
    pfilter.TimeRangeCache.ResetTimeConstraints()

    self._temp_directory = tempfile.mkdtemp()

  def tearDown(self):
    """Cleans up the objects used throughout the test."""
    shutil.rmtree(self._temp_directory, True)

  def _GetTestScanNode(self, scan_context):
    """Retrieves the scan node for testing.

    Retrieves the first scan node, from the root upwards, with more or less
    than 1 sub node.

    Args:
      scan_context: scan context (instance of dfvfs.ScanContext).

    Returns:
      A scan node (instance of dfvfs.ScanNode).
    """
    scan_node = scan_context.GetRootScanNode()
    while len(scan_node.sub_nodes) == 1:
      scan_node = scan_node.sub_nodes[0]

    return scan_node

  def testHashing(self):
    """Tests hashing functionality."""
    self._GetTestFilePath([u'ímynd.dd'])

    # TODO: implement test.

  def testGetHashersInformation(self):
    """Tests the GetHashersInformation function."""
    test_front_end = extraction_frontend.ExtractionFrontend()
    hashers_information = test_front_end.GetHashersInformation()

    self.assertGreaterEqual(len(hashers_information), 3)
    available_hasher_names = []
    for name, _ in hashers_information:
      available_hasher_names.append(name)

    self.assertIn(u'sha1', available_hasher_names)
    self.assertIn(u'sha256', available_hasher_names)

  def testGetParserPluginsInformation(self):
    """Tests the GetParserPluginsInformation function."""
    test_front_end = extraction_frontend.ExtractionFrontend()
    parser_plugins_information = test_front_end.GetParserPluginsInformation()

    self.assertGreaterEqual(len(parser_plugins_information), 1)
    available_parser_names = []
    for name, _ in parser_plugins_information:
      available_parser_names.append(name)

    self.assertIn(u'olecf_default', available_parser_names)

  def testGetParserPresetsInformation(self):
    """Tests the GetParserPresetsInformation function."""
    test_front_end = extraction_frontend.ExtractionFrontend()
    parser_presets_information = test_front_end.GetParserPresetsInformation()

    self.assertGreaterEqual(len(parser_presets_information), 1)
    available_parser_names = []
    for name, _ in parser_presets_information:
      available_parser_names.append(name)

    self.assertIn(u'linux', available_parser_names)

  def testGetParsersInformation(self):
    """Tests the GetParsersInformation function."""
    test_front_end = extraction_frontend.ExtractionFrontend()
    parsers_information = test_front_end.GetParsersInformation()

    self.assertGreaterEqual(len(parsers_information), 1)
    available_parser_names = []
    for name, _ in parsers_information:
      available_parser_names.append(name)

    self.assertIn(u'filestat', available_parser_names)

  # Note: this test takes multiple seconds to complete due to
  # the behavior of the multi processing queue.
  def testProcessSources(self):
    """Tests the ProcessSources function."""
    test_front_end = extraction_frontend.ExtractionFrontend()
    storage_file_path = os.path.join(self._temp_directory, u'plaso.db')
    test_front_end.SetStorageFile(storage_file_path=storage_file_path)

    test_file = self._GetTestFilePath([u'ímynd.dd'])
    volume_path_spec = path_spec_factory.Factory.NewPathSpec(
        dfvfs_definitions.TYPE_INDICATOR_OS, location=test_file)
    path_spec = path_spec_factory.Factory.NewPathSpec(
        dfvfs_definitions.TYPE_INDICATOR_TSK, location=u'/',
        parent=volume_path_spec)

    # TODO: move source_scanner.SourceScannerContext.SOURCE_TYPE_
    # to definitions.SOURCE_TYPE_.
    source_type = (
        source_scanner.SourceScannerContext.SOURCE_TYPE_STORAGE_MEDIA_IMAGE)

    test_front_end.ProcessSources([path_spec], source_type)

    try:
      storage_file = storage_zip_file.StorageFile(
          storage_file_path, read_only=True)
    except IOError:
      self.fail(u'Not a storage file.')

    # Make sure we can read an event out of the storage.
    event_object = storage_file.GetSortedEntry()
    self.assertIsNotNone(event_object)


if __name__ == '__main__':
  unittest.main()
