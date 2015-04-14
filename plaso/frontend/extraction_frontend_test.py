#!/usr/bin/python
# -*- coding: utf-8 -*-
"""Tests for the extraction front-end object."""

import os
import shutil
import tempfile
import unittest

from plaso.frontend import extraction_frontend
from plaso.frontend import frontend
from plaso.frontend import test_lib
from plaso.lib import pfilter
from plaso.lib import storage


class ExtractionFrontendTests(test_lib.FrontendTestCase):
  """Tests for the extraction front-end object."""

  def setUp(self):
    """Sets up the objects used throughout the test."""
    # This is necessary since TimeRangeCache uses class members.
    # TODO: remove this work around and properly fix TimeRangeCache.
    pfilter.TimeRangeCache.ResetTimeConstraints()

    self._input_reader = frontend.StdinFrontendInputReader()
    self._output_writer = frontend.StdoutFrontendOutputWriter()
    self._temp_directory = tempfile.mkdtemp()

  def tearDown(self):
    """Cleans up the objects used throughout the test."""
    shutil.rmtree(self._temp_directory, True)

  def testHashing(self):
    """Tests hashing functionality."""
    self._GetTestFilePath([u'ímynd.dd'])

    # TODO: implement test.

  def testProcessSource(self):
    """Tests the ProcessSource function."""
    test_front_end = extraction_frontend.ExtractionFrontend()
    source_file = self._GetTestFilePath([u'ímynd.dd'])
    storage_file_path = os.path.join(self._temp_directory, u'plaso.db')

    # TODO: refactor this.
    options = frontend.Options()

    test_front_end.SetStorageFile(storage_file_path=storage_file_path)

    test_front_end.ScanSource(source_file)
    test_front_end.ProcessSource(options)

    try:
      storage_file = storage.StorageFile(storage_file_path, read_only=True)
    except IOError:
      self.fail(u'Not a storage file.')

    # Make sure we can read an event out of the storage.
    event_object = storage_file.GetSortedEntry()
    self.assertIsNotNone(event_object)


if __name__ == '__main__':
  unittest.main()
