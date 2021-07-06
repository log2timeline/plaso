#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""Tests for the storage writer."""

import unittest

from plaso.storage import writer

from tests.storage import test_lib


class StorageWriterTest(test_lib.StorageTestCase):
  """Tests for the storage writer."""

  # pylint: disable=protected-access

  def testRaiseIfNotWritable(self):
    """Tests the _RaiseIfNotWritable function."""
    storage_writer = writer.StorageWriter()

    with self.assertRaises(IOError):
      storage_writer._RaiseIfNotWritable()

  def testSetSerializersProfiler(self):
    """Tests the SetSerializersProfiler function."""
    storage_writer = writer.StorageWriter()

    storage_writer.SetSerializersProfiler(None)

  def testSetStorageProfiler(self):
    """Tests the SetStorageProfiler function."""
    storage_writer = writer.StorageWriter()

    storage_writer.SetStorageProfiler(None)


if __name__ == '__main__':
  unittest.main()
