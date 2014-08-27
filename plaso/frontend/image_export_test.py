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
"""Tests for the image export front-end."""

import glob
import os
import shutil
import tempfile
import unittest

from plaso.frontend import image_export
from plaso.frontend import test_lib


class Log2TimelineFrontendTest(test_lib.FrontendTestCase):
  """Tests for the image export front-end."""

  def setUp(self):
    """Sets up the objects used throughout the test."""
    self._temp_directory = tempfile.mkdtemp()

  def tearDown(self):
    """Cleans up the objects used throughout the test."""
    shutil.rmtree(self._temp_directory, True)

  def testProcessSource(self):
    """Tests the process source function."""
    test_front_end = image_export.ImageExportFrontend()

    options = test_lib.Options()
    options.image = self._GetTestFilePath(['image.qcow2'])
    options.path = self._temp_directory
    options.extension_string = 'txt'

    test_front_end.ParseOptions(options, source_option='image')

    test_front_end.ProcessSource(options)

    expexted_text_files = sorted([
      os.path.join(self._temp_directory, 'passwords.txt')])

    text_files = glob.glob(os.path.join(self._temp_directory, '*.txt'))

    self.assertEquals(sorted(text_files), expexted_text_files)

    # TODO: add more tests that cover more of the functionality of the frontend.


if __name__ == '__main__':
  unittest.main()
