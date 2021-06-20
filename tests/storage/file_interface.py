#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""Tests for the storage interface classes."""

import unittest

from plaso.storage import file_interface


class BaseStorageFileTest(unittest.TestCase):
  """Tests for the file-based stores interface."""

  def testInitialization(self):
    """Tests the __init__ function."""
    test_storage = file_interface.BaseStorageFile()
    self.assertIsNotNone(test_storage)

  # TODO: add more tests.


# TODO: add tests for StorageFileReader
# TODO: add tests for StorageFileWriter


if __name__ == '__main__':
  unittest.main()
