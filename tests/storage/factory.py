#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""Tests for the storage factory."""

import unittest

from plaso.storage import factory
from plaso.storage.sqlite import reader as sqlite_reader
from plaso.storage.sqlite import writer as sqlite_writer

from tests.storage import test_lib


class StorageFactoryTest(test_lib.StorageTestCase):
  """Tests for the storage factory."""

  def testCreateStorageReaderForFile(self):
    """Test the CreateStorageReaderForFile function."""
    test_file_path = self._GetTestFilePath(['psort_test.plaso'])
    self._SkipIfPathNotExists(test_file_path)

    storage_reader = factory.StorageFactory.CreateStorageReaderForFile(
        test_file_path)
    self.assertIsInstance(storage_reader, sqlite_reader.SQLiteStorageFileReader)

  def testCreateStorageWriterForFile(self):
    """Test the CreateStorageWriterForFile function."""
    test_file_path = self._GetTestFilePath(['psort_test.plaso'])
    self._SkipIfPathNotExists(test_file_path)

    storage_reader = factory.StorageFactory.CreateStorageWriterForFile(
        test_file_path)
    self.assertIsInstance(storage_reader, sqlite_writer.SQLiteStorageFileWriter)


if __name__ == '__main__':
  unittest.main()
