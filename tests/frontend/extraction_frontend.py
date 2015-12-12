#!/usr/bin/python
# -*- coding: utf-8 -*-
"""Tests for the extraction front-end object."""

import os
import unittest

from dfvfs.lib import definitions as dfvfs_definitions
from dfvfs.path import factory as path_spec_factory

from plaso.frontend import extraction_frontend
from plaso.storage import zip_file as storage_zip_file

from tests import test_lib as shared_test_lib
from tests.frontend import test_lib


class ExtractionFrontendTests(test_lib.FrontendTestCase):
  """Tests for the extraction front-end object."""

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

  # TODO: add test for _CheckStorageFile
  # TODO: add test for _GetParserFilterPreset
  # TODO: add test for _PreprocessSource
  # TODO: add test for _PreprocessSetCollectionInformation
  # TODO: add test for _PreprocessSetTimezone

  def testGetHashersInformation(self):
    """Tests the GetHashersInformation function."""
    test_front_end = extraction_frontend.ExtractionFrontend()
    hashers_information = test_front_end.GetHashersInformation()

    self.assertGreaterEqual(len(hashers_information), 3)

    available_hasher_names = [name for name, _ in hashers_information]
    self.assertIn(u'sha1', available_hasher_names)
    self.assertIn(u'sha256', available_hasher_names)

  def testGetParserPluginsInformation(self):
    """Tests the GetParserPluginsInformation function."""
    test_front_end = extraction_frontend.ExtractionFrontend()
    parser_plugins_information = test_front_end.GetParserPluginsInformation()

    self.assertGreaterEqual(len(parser_plugins_information), 1)

    available_parser_names = [name for name, _ in parser_plugins_information]
    self.assertIn(u'olecf_default', available_parser_names)

  def testGetParserPresetsInformation(self):
    """Tests the GetParserPresetsInformation function."""
    test_front_end = extraction_frontend.ExtractionFrontend()
    parser_presets_information = test_front_end.GetParserPresetsInformation()

    self.assertGreaterEqual(len(parser_presets_information), 1)

    available_parser_names = [name for name, _ in parser_presets_information]
    self.assertIn(u'linux', available_parser_names)

  def testGetParsersInformation(self):
    """Tests the GetParsersInformation function."""
    test_front_end = extraction_frontend.ExtractionFrontend()
    parsers_information = test_front_end.GetParsersInformation()

    self.assertGreaterEqual(len(parsers_information), 1)

    available_parser_names = [name for name, _ in parsers_information]
    self.assertIn(u'filestat', available_parser_names)

  def testGetNamesOfParsersWithPlugins(self):
    """Tests the GetNamesOfParsersWithPlugins function."""
    test_front_end = extraction_frontend.ExtractionFrontend()
    parsers_names = test_front_end.GetNamesOfParsersWithPlugins()

    self.assertGreaterEqual(len(parsers_names), 1)

    self.assertIn(u'winreg', parsers_names)

  # Note: this test takes multiple seconds to complete due to
  # the behavior of the multi processing queue.
  def testProcessSources(self):
    """Tests the ProcessSources function."""
    test_front_end = extraction_frontend.ExtractionFrontend()

    test_file = self._GetTestFilePath([u'ímynd.dd'])
    volume_path_spec = path_spec_factory.Factory.NewPathSpec(
        dfvfs_definitions.TYPE_INDICATOR_OS, location=test_file)
    path_spec = path_spec_factory.Factory.NewPathSpec(
        dfvfs_definitions.TYPE_INDICATOR_TSK, location=u'/',
        parent=volume_path_spec)

    source_type = dfvfs_definitions.SOURCE_TYPE_STORAGE_MEDIA_IMAGE

    with shared_test_lib.TempDirectory() as temp_directory:
      storage_file_path = os.path.join(temp_directory, u'plaso.db')
      test_front_end.SetStorageFile(storage_file_path=storage_file_path)

      test_front_end.ProcessSources([path_spec], source_type)

      try:
        storage_file = storage_zip_file.StorageFile(
            storage_file_path, read_only=True)
      except IOError:
        self.fail(u'Unable to open storage file after processing.')

      # Make sure we can read events from the storage.
      event_object = storage_file.GetSortedEntry()
      self.assertIsNotNone(event_object)

      self.assertGreaterEqual(event_object.data_type, u'fs:stat')
      self.assertGreaterEqual(event_object.filename, u'/lost+found')

  def testSetDebugMode(self):
    """Tests the SetDebugMode function."""
    test_front_end = extraction_frontend.ExtractionFrontend()
    test_front_end.SetDebugMode(enable_debug=True)

  def testSetEnablePreprocessing(self):
    """Tests the SetEnablePreprocessing function."""
    test_front_end = extraction_frontend.ExtractionFrontend()
    test_front_end.SetEnablePreprocessing(True)

  def testSetEnableProfiling(self):
    """Tests the SetEnableProfiling function."""
    test_front_end = extraction_frontend.ExtractionFrontend()
    test_front_end.SetEnableProfiling(
        True, profiling_sample_rate=5000, profiling_type=u'all')

  def testSetShowMemoryInformation(self):
    """Tests the SetShowMemoryInformation function."""
    test_front_end = extraction_frontend.ExtractionFrontend()
    test_front_end.SetShowMemoryInformation(show_memory=False)

  def testSetStorageFile(self):
    """Tests the SetStorageFile function."""
    test_front_end = extraction_frontend.ExtractionFrontend()
    test_front_end.SetStorageFile(u'/tmp/test.plaso')

  def testSetTextPrepend(self):
    """Tests the SetTextPrepend function."""
    test_front_end = extraction_frontend.ExtractionFrontend()
    test_front_end.SetTextPrepend(u'prepended text')

  def testSetUseOldPreprocess(self):
    """Tests the SetUseOldPreprocess function."""
    test_front_end = extraction_frontend.ExtractionFrontend()
    test_front_end.SetUseOldPreprocess(True)

  def testSetUseZeroMQ(self):
    """Tests the SetUseZeroMQ function."""
    test_front_end = extraction_frontend.ExtractionFrontend()
    test_front_end.SetUseZeroMQ(use_zeromq=True)


if __name__ == '__main__':
  unittest.main()
