#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""Tests for the SQLite-based storage file reader."""

import unittest

from plaso.storage.sqlite import reader

from tests.storage import test_lib


class SQLiteStorageFileReaderTest(test_lib.StorageTestCase):
  """Tests for the SQLite-based storage file reader."""

  def testInitialization(self):
    """Tests the __init__ function."""
    test_path = self._GetTestFilePath(['pinfo_test.plaso'])
    test_reader = reader.SQLiteStorageFileReader(test_path)
    self.assertIsNotNone(test_reader)


if __name__ == '__main__':
  unittest.main()
