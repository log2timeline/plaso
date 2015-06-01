#!/usr/bin/python
# -*- coding: utf-8 -*-
"""Tests for the extraction front-end object."""

import os
import shutil
import tempfile
import unittest

from dfvfs.lib import definitions as dfvfs_definitions

from plaso.frontend import extraction_frontend
from plaso.frontend import test_lib
from plaso.lib import pfilter
from plaso.lib import storage


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

  # Note: this test takes multiple seconds to complete due to
  # the behavior of the multi processing queue.
  def testProcessSources(self):
    """Tests the ProcessSources function."""
    test_front_end = extraction_frontend.ExtractionFrontend()
    source_file = self._GetTestFilePath([u'ímynd.dd'])
    storage_file_path = os.path.join(self._temp_directory, u'plaso.db')

    test_front_end.SetStorageFile(storage_file_path=storage_file_path)

    scan_context = test_front_end.ScanSource(source_file)

    scan_node = self._GetTestScanNode(scan_context)
    self.assertNotEqual(scan_node, None)
    self.assertEqual(
        scan_node.type_indicator, dfvfs_definitions.TYPE_INDICATOR_TSK)

    test_front_end.ProcessSources([scan_node.path_spec])

    try:
      storage_file = storage.StorageFile(storage_file_path, read_only=True)
    except IOError:
      self.fail(u'Not a storage file.')

    # Make sure we can read an event out of the storage.
    event_object = storage_file.GetSortedEntry()
    self.assertIsNotNone(event_object)


if __name__ == '__main__':
  unittest.main()
