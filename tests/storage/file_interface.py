#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""Tests for the storage interface classes."""

from __future__ import unicode_literals

import unittest

from plaso.storage import file_interface


class SerializedAttributeContainerListTest(unittest.TestCase):
  """Tests for the serialized attribute container list."""

  # pylint: disable=protected-access

  # TODO: add tests for number_of_attribute_containers property

  def testEmpty(self):
    """Tests the Empty function."""
    container_list = file_interface.SerializedAttributeContainerList()

    container_list.Empty()
    self.assertEqual(container_list._list, [])

    # TODO: improve test coverage.

  # TODO: add tests for GetAttributeContainerByIndex function
  # TODO: add tests for PopAttributeContainer function
  # TODO: add tests for PushAttributeContainer function


# TODO: add tests for BaseStorageFile
# TODO: add tests for StorageFileMergeReader
# TODO: add tests for StorageFileReader
# TODO: add tests for StorageFileWriter


if __name__ == '__main__':
  unittest.main()
