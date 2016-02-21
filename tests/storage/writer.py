#!/usr/bin/python
# -*- coding: utf-8 -*-
"""Tests for the storage writer."""

import os
import unittest
import zipfile

from plaso.engine import queue
from plaso.lib import event
from plaso.multi_processing import multi_process
from plaso.formatters import winreg   # pylint: disable=unused-import
from plaso.storage import writer

from tests import test_lib as shared_test_lib
from tests.storage import test_lib


class FileStorageWriterTest(unittest.TestCase):
  """Tests for the file storage writer."""

  def testStorageWriter(self):
    """Test the storage writer."""
    test_event_objects = test_lib.CreateTestEventObjects()

    # The storage writer is normally run in a separate thread.
    # For the purpose of this test it has to be run in sequence,
    # hence the call to WriteEventObjects after all the event objects
    # have been queued up.

    # TODO: add upper queue limit.
    # A timeout is used to prevent the multi processing queue to close and
    # stop blocking the current process.
    test_queue = multi_process.MultiProcessingQueue(timeout=0.1)
    test_queue_producer = queue.ItemQueueProducer(test_queue)
    test_queue_producer.ProduceItems(test_event_objects)

    test_queue_producer.SignalAbort()

    preprocessing_object = event.PreprocessObject()

    with shared_test_lib.TempDirectory() as temp_directory:
      temp_file = os.path.join(temp_directory, u'plaso.db')
      storage_writer = writer.FileStorageWriter(
          test_queue, temp_file, preprocessing_object)
      storage_writer.WriteEventObjects()

      zip_file = zipfile.ZipFile(
          temp_file, mode='r', compression=zipfile.ZIP_DEFLATED)

      expected_filename_list = [
          u'information.dump', u'plaso_index.000001', u'plaso_meta.000001',
          u'plaso_proto.000001', u'plaso_timestamps.000001', u'serializer.txt']

      filename_list = sorted(zip_file.namelist())
      self.assertEqual(len(filename_list), 6)
      self.assertEqual(filename_list, expected_filename_list)


# TODO: add BypassStorageWriterTest


if __name__ == '__main__':
  unittest.main()
