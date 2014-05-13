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
"""Tests for test pinfo front-end."""

import os
import unittest

from plaso.frontend import pinfo
from plaso.frontend import test_lib


class PinfoFrontendTest(test_lib.FrontendTestCase):
  """Tests for test pinfo front-end."""

  def testGetStorageInformation(self):
    """Tests the get storage information function."""
    test_front_end = pinfo.PinfoFrontend()

    options = test_lib.Options()
    options.storage_file = os.path.join(self._TEST_DATA_PATH, 'psort_test.out')

    test_front_end.ParseOptions(options)

    storage_information_list = list(test_front_end.GetStorageInformation())

    self.assertEquals(len(storage_information_list), 1)

    lines_of_text = storage_information_list[0].split(u'\n')

    expected_line_of_text = u'-' * 80
    self.assertEquals(lines_of_text[0], expected_line_of_text)
    self.assertEquals(lines_of_text[2], expected_line_of_text)

    self.assertEquals(lines_of_text[1], u'\t\tPlaso Storage Information')

    expected_line_of_text = u'Storage file:\t\t{0:s}'.format(
        options.storage_file)
    self.assertEquals(lines_of_text[3], expected_line_of_text)

    self.assertEquals(lines_of_text[4], u'Source processed:\tsyslog')

    expected_line_of_text = u'Time of processing:\t2014-02-15T04:33:16+00:00'
    self.assertEquals(lines_of_text[5], expected_line_of_text)

    self.assertEquals(lines_of_text[6], u'')
    self.assertEquals(lines_of_text[7], u'Collection information:')


if __name__ == '__main__':
  unittest.main()
