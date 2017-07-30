#!/usr/bin/python
# -*- coding: utf-8 -*-
"""Tests for the storage factory."""

import unittest

from plaso.containers import sessions
from plaso.storage import factory
from plaso.storage import zip_file

from tests import test_lib as shared_test_lib
from tests.storage import test_lib


class StorageFactoryTest(test_lib.StorageTestCase):
  """Tests for the storage factory."""

  @shared_test_lib.skipUnlessHasTestFile([u'psort_test.json.plaso'])
  def testCreateStorageFileForFile(self):
    """Test the CreateStorageFileForFile function."""
    test_file = self._GetTestFilePath([u'psort_test.json.plaso'])

    storage_file = factory.StorageFactory.CreateStorageFileForFile(test_file)
    self.assertIsInstance(storage_file, zip_file.ZIPStorageFile)

  @shared_test_lib.skipUnlessHasTestFile([u'psort_test.json.plaso'])
  def testCreateStorageReaderForFile(self):
    """Test the CreateStorageReaderForFile function."""
    test_file = self._GetTestFilePath([u'psort_test.json.plaso'])

    storage_reader = factory.StorageFactory.CreateStorageReaderForFile(
        test_file)
    self.assertIsInstance(storage_reader, zip_file.ZIPStorageFileReader)

  @shared_test_lib.skipUnlessHasTestFile([u'psort_test.json.plaso'])
  def testCreateStorageWriterForFile(self):
    """Test the CreateStorageWriterForFile function."""
    session = sessions.Session()
    test_file = self._GetTestFilePath([u'psort_test.json.plaso'])

    storage_reader = factory.StorageFactory.CreateStorageWriterForFile(
        session, test_file)
    self.assertIsInstance(storage_reader, zip_file.ZIPStorageFileWriter)


if __name__ == '__main__':
  unittest.main()
