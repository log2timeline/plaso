#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""Tests for the storage factory."""

from __future__ import unicode_literals

import unittest

from plaso.containers import sessions
from plaso.storage import factory
from plaso.storage.sqlite import reader as sqlite_reader
from plaso.storage.sqlite import writer as sqlite_writer

from tests import test_lib as shared_test_lib
from tests.storage import test_lib


class StorageFactoryTest(test_lib.StorageTestCase):
  """Tests for the storage factory."""

  @shared_test_lib.skipUnlessHasTestFile(['psort_test.plaso'])
  def testCreateStorageReaderForFile(self):
    """Test the CreateStorageReaderForFile function."""
    test_file = self._GetTestFilePath(['psort_test.plaso'])

    storage_reader = factory.StorageFactory.CreateStorageReaderForFile(
        test_file)
    self.assertIsInstance(
        storage_reader, sqlite_reader.SQLiteStorageFileReader)

  @shared_test_lib.skipUnlessHasTestFile(['psort_test.plaso'])
  def testCreateStorageWriterForFile(self):
    """Test the CreateStorageWriterForFile function."""
    session = sessions.Session()
    test_file = self._GetTestFilePath(['psort_test.plaso'])

    storage_reader = factory.StorageFactory.CreateStorageWriterForFile(
        session, test_file)
    self.assertIsInstance(
        storage_reader, sqlite_writer.SQLiteStorageFileWriter)


if __name__ == '__main__':
  unittest.main()
