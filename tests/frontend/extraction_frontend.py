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


class ExtractionFrontendTests(shared_test_lib.BaseTestCase):
  """Tests for the extraction front-end object."""

  # pylint: disable=protected-access

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
  # TODO: add test for _SetDefaultTimezone

  def testEnableAndDisableProfiling(self):
    """Tests the EnableProfiling and DisableProfiling functions."""
    test_front_end = extraction_frontend.ExtractionFrontend()

    self.assertFalse(test_front_end._enable_profiling)

    test_front_end.EnableProfiling()
    self.assertTrue(test_front_end._enable_profiling)

    test_front_end.DisableProfiling()
    self.assertFalse(test_front_end._enable_profiling)

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
      storage_file_path = os.path.join(temp_directory, u'storage.plaso')
      test_front_end.SetStorageFile(storage_file_path)

      test_front_end.ProcessSources([path_spec], source_type)

      storage_file = storage_zip_file.ZIPStorageFile()
      try:
        storage_file.Open(path=storage_file_path)
      except IOError:
        self.fail(u'Unable to open storage file after processing.')

      # Make sure we can read events from the storage.
      event_objects = list(storage_file.GetEvents())
      self.assertNotEqual(len(event_objects), 0)

      event_object = event_objects[0]

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

  def testSetShowMemoryInformation(self):
    """Tests the SetShowMemoryInformation function."""
    test_front_end = extraction_frontend.ExtractionFrontend()
    test_front_end.SetShowMemoryInformation(show_memory=False)

  def testSetStorageFile(self):
    """Tests the SetStorageFile function."""
    test_front_end = extraction_frontend.ExtractionFrontend()
    test_front_end.SetStorageFile(u'/tmp/storage.plaso')

  def testSetTextPrepend(self):
    """Tests the SetTextPrepend function."""
    test_front_end = extraction_frontend.ExtractionFrontend()
    test_front_end.SetTextPrepend(u'prepended text')

  def testSetUseZeroMQ(self):
    """Tests the SetUseZeroMQ function."""
    test_front_end = extraction_frontend.ExtractionFrontend()
    test_front_end.SetUseZeroMQ(use_zeromq=True)


if __name__ == '__main__':
  unittest.main()
