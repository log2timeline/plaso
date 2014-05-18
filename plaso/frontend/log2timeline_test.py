#!/usr/bin/python
# -*- coding: utf-8 -*-
#
# Copyright 2014 The Plaso Project Authors.
# Please see the AUTHORS file for details on individual authors.
#
# Licensed under the Apache License, Version 2.0 (the "License");
# you may not use this file except in compliance with the License.
# You may obtain a copy of the License at
#
#    http://www.apache.org/licenses/LICENSE-2.0
#
# Unless required by applicable law or agreed to in writing, software
# distributed under the License is distributed on an "AS IS" BASIS,
# WITHOUT WARRANTIES OR CONDITIONS OF ANY KIND, either express or implied.
# See the License for the specific language governing permissions and
# limitations under the License.
"""Tests for the log2timeline front-end."""

import os
import shutil
import tempfile
import unittest

from plaso.frontend import log2timeline
from plaso.frontend import test_lib
from plaso.lib import storage


class Log2TimelineFrontendTest(test_lib.FrontendTestCase):
  """Tests for the log2timeline front-end."""

  def setUp(self):
    """Sets up the objects used throughout the test."""
    self._temp_directory = tempfile.mkdtemp()

  def tearDown(self):
    """Cleans up the objects used throughout the test."""
    shutil.rmtree(self._temp_directory, True)

  def testGetStorageInformation(self):
    """Tests the get storage information function."""
    test_front_end = log2timeline.Log2TimelineFrontend()

    options = test_lib.Options()
    options.source = self._GetTestFilePath(['image.dd'])

    storage_file_path = os.path.join(self._temp_directory, 'plaso.db')

    test_front_end.ParseOptions(options, 'source')
    test_front_end.SetStorageFile(storage_file_path=storage_file_path)
    test_front_end.SetRunForeman(run_foreman=False)

    test_front_end.ProcessSource(options)

    try:
      storage_file = storage.StorageFile(storage_file_path, read_only=True)
    except IOError:
      # This is not a storage file, we should fail.
      self.assertTrue(False)

    # Make sure we can read an event out of the storage.
    event_object = storage_file.GetSortedEntry()
    self.assertIsNotNone(event_object)

    # TODO: add more tests that cover more of the functionality of the frontend.


if __name__ == '__main__':
  unittest.main()
