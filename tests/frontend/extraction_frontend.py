#!/usr/bin/python
# -*- coding: utf-8 -*-
"""Tests for the extraction front-end object."""

import os
import unittest

from dfvfs.lib import definitions as dfvfs_definitions
from dfvfs.path import factory as path_spec_factory

from plaso.containers import sessions
from plaso.engine import configurations
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
  # TODO: add test for _PreprocessSource
  # TODO: add test for _PreprocessSetCollectionInformation
  # TODO: add test for _SetTimezone

  # Note: this test takes multiple seconds to complete due to
  # the behavior of the multi processing queue.
  @shared_test_lib.skipUnlessHasTestFile([u'ímynd.dd'])
  def testProcessSources(self):
    """Tests the ProcessSources function."""
    session = sessions.Session()
    test_front_end = extraction_frontend.ExtractionFrontend()

    test_file = self._GetTestFilePath([u'ímynd.dd'])
    volume_path_spec = path_spec_factory.Factory.NewPathSpec(
        dfvfs_definitions.TYPE_INDICATOR_OS, location=test_file)
    path_spec = path_spec_factory.Factory.NewPathSpec(
        dfvfs_definitions.TYPE_INDICATOR_TSK, location=u'/',
        parent=volume_path_spec)

    source_type = dfvfs_definitions.SOURCE_TYPE_STORAGE_MEDIA_IMAGE

    configuration = configurations.ProcessingConfiguration()

    with shared_test_lib.TempDirectory() as temp_directory:
      storage_file_path = os.path.join(temp_directory, u'storage.plaso')

      storage_writer = storage_zip_file.ZIPStorageFileWriter(
          session, storage_file_path)
      test_front_end.ProcessSources(
          session, storage_writer, [path_spec], source_type, configuration)

      storage_file = storage_zip_file.ZIPStorageFile()
      try:
        storage_file.Open(path=storage_file_path)
      except IOError:
        self.fail(u'Unable to open storage file after processing.')

      # Make sure we can read events from the storage.
      event_objects = list(storage_file.GetEvents())
      self.assertNotEqual(len(event_objects), 0)

      event_object = event_objects[0]

      self.assertEqual(event_object.data_type, u'fs:stat')
      self.assertEqual(event_object.filename, u'/lost+found')


if __name__ == '__main__':
  unittest.main()
