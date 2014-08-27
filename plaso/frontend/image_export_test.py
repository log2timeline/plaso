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

  def testProcessSourceExtractWithExtensions(self):
    """Tests extract with extensions process source functionality."""
    test_front_end = image_export.ImageExportFrontend()

    options = test_lib.Options()
    options.image = self._GetTestFilePath([u'image.qcow2'])
    options.path = self._temp_directory
    options.extension_string = u'txt'

    test_front_end.ParseOptions(options, source_option='image')

    test_front_end.ProcessSource(options)

    expected_text_files = sorted([
      os.path.join(self._temp_directory, u'passwords.txt')])

    text_files = glob.glob(os.path.join(self._temp_directory, u'*'))

    self.assertEquals(sorted(text_files), expected_text_files)

  def testProcessSourceExtractWithFilter(self):
    """Tests extract with filter process source functionality."""
    test_front_end = image_export.ImageExportFrontend()

    options = test_lib.Options()
    options.image = self._GetTestFilePath([u'image.qcow2'])
    options.path = self._temp_directory

    options.filter = os.path.join(self._temp_directory, u'filter.txt')
    with open(options.filter, 'wb') as file_object:
      file_object.write('/a_directory/.+_file\n')

    test_front_end.ParseOptions(options, source_option='image')

    test_front_end.ProcessSource(options)

    expected_text_files = sorted([
      os.path.join(self._temp_directory, u'a_directory', u'another_file'),
      os.path.join(self._temp_directory, u'a_directory', u'a_file')])

    text_files = glob.glob(os.path.join(
        self._temp_directory, u'a_directory', u'*'))

    self.assertEquals(sorted(text_files), expected_text_files)


if __name__ == '__main__':
  unittest.main()
