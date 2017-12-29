#!/usr/bin/python
# -*- coding: utf-8 -*-
"""Tests for the storage factory."""

from __future__ import unicode_literals

import unittest

from plaso.containers import sessions
from plaso.storage import factory
from plaso.storage import sqlite_file

from tests import test_lib as shared_test_lib
from tests.storage import test_lib


class StorageFactoryTest(test_lib.StorageTestCase):
  """Tests for the storage factory."""

  @shared_test_lib.skipUnlessHasTestFile(['psort_test.json.plaso'])
  def testCreateStorageFileForFile(self):
    """Test the CreateStorageFileForFile function."""
    test_file = self._GetTestFilePath(['psort_test.json.plaso'])

    storage_file = factory.StorageFactory.CreateStorageFileForFile(test_file)
    self.assertIsInstance(storage_file, sqlite_file.SQLiteStorageFile)

  @shared_test_lib.skipUnlessHasTestFile(['psort_test.json.plaso'])
  def testCreateStorageReaderForFile(self):
    """Test the CreateStorageReaderForFile function."""
    test_file = self._GetTestFilePath(['psort_test.json.plaso'])

    storage_reader = factory.StorageFactory.CreateStorageReaderForFile(
        test_file)
    self.assertIsInstance(storage_reader, sqlite_file.SQLiteStorageFileReader)

  @shared_test_lib.skipUnlessHasTestFile(['psort_test.json.plaso'])
  def testCreateStorageWriterForFile(self):
    """Test the CreateStorageWriterForFile function."""
    session = sessions.Session()
    test_file = self._GetTestFilePath(['psort_test.json.plaso'])

    storage_reader = factory.StorageFactory.CreateStorageWriterForFile(
        session, test_file)
    self.assertIsInstance(storage_reader, sqlite_file.SQLiteStorageFileWriter)


if __name__ == '__main__':
  unittest.main()
