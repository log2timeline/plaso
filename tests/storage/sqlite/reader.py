#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""Tests for the SQLite-based storage reader."""

import unittest

from plaso.storage.sqlite import reader

from tests.storage import test_lib


class SQLiteStorageReaderTest(test_lib.StorageTestCase):
  """Tests for the SQLite-based storage reader."""

  def testInitialization(self):
    """Tests the __init__ function."""
    test_path = self._GetTestFilePath(['pinfo_test.plaso'])
    test_reader = reader.SQLiteStorageReader(test_path)
    self.assertIsNotNone(test_reader)


if __name__ == '__main__':
  unittest.main()
