#!/usr/bin/python
# -*- coding: utf-8 -*-
"""Tests for plaso.output.pstorage."""

import os
import unittest

from plaso.output import event_buffer
from plaso.output import pstorage
from plaso.storage import reader
from plaso.storage import zip_file as storage_zip_file

from tests import test_lib as shared_test_lib
from tests.output import test_lib


class PstorageTest(test_lib.OutputModuleTestCase):
  """Tests for the plaso storage outputter."""

  def testOutput(self):
    """Tests the Output function."""
    test_filename = os.path.join(u'test_data', u'psort_test.json.plaso')

    with shared_test_lib.TempDirectory() as temp_directory:
      temp_file = os.path.join(temp_directory, u'pstorage.plaso')

      storage_file = storage_zip_file.StorageFile(test_filename, read_only=True)
      with reader.StorageObjectReader(storage_file) as storage_reader:

        output_mediator = self._CreateOutputMediator(storage_file=storage_file)
        output_module = pstorage.PlasoStorageOutputModule(output_mediator)

        output_module.SetFilePath(temp_file)

        with event_buffer.EventBuffer(
            output_module, check_dedups=False) as output_buffer:
          for event_object in storage_reader.GetEvents():
            output_buffer.Append(event_object)

      original_zip_file = storage_zip_file.StorageFile(
          test_filename, read_only=True)
      pstorage_zip_file = storage_zip_file.StorageFile(
          temp_file, read_only=True)

      original_list = []
      pstorage_list = []

      event_object_original = original_zip_file.GetSortedEntry()
      event_object_pstorage = pstorage_zip_file.GetSortedEntry()
      while event_object_original:
        original_equality_string = event_object_original.EqualityString()
        pstorage_equality_string = event_object_pstorage.EqualityString()

	# Remove the UUID for comparision.
        original_equality_string, _, _ = original_equality_string.rpartition(
            u'|')
        pstorage_equality_string, _, _ = pstorage_equality_string.rpartition(
            u'|')

        original_list.append(original_equality_string)
        pstorage_list.append(pstorage_equality_string)

        event_object_original = original_zip_file.GetSortedEntry()
        event_object_pstorage = pstorage_zip_file.GetSortedEntry()

      self.assertFalse(event_object_pstorage)

      for original_str, dump_str in zip(
          sorted(original_list), sorted(pstorage_list)):
        self.assertEqual(original_str, dump_str)


if __name__ == '__main__':
  unittest.main()
