#!/usr/bin/python
# -*- coding: utf-8 -*-
# Copyright 2012 Google Inc. All Rights Reserved.
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
"""This file contains a test for MRU registry parsing in Plaso."""
import unittest

from plaso.lib import eventdata
from plaso.registry import default
from plaso.registry import test_lib


class TestDefaultRegistry(unittest.TestCase):
  """The unit test for default registry key parsing."""

  def setUp(self):
    """Sets up the needed objects used throughout the test."""
    values = []
    values.append(test_lib.TestRegValue('MRUList', 'acb'.encode('utf_16_le'),
                                        1, 123))
    values.append(test_lib.TestRegValue(
        'a', 'Some random text here'.encode('utf_16_le'), 1, 1892))
    values.append(test_lib.TestRegValue(
        'b', 'c:/evil.exe'.encode('utf_16_le'), 3, 612))
    values.append(test_lib.TestRegValue(
        'c', 'C:/looks_legit.exe'.encode('utf_16_le'), 1, 1001))

    self.regkey = test_lib.TestRegKey(
        '\\Microsoft\\Some Windows\\InterestingApp\\MRU', 1346145829002031,
        values, 1456)

  def testDefault(self):
    """Run a simple test against a mocked MRU list."""
    plugin = default.DefaultPlugin(None)
    generator = plugin.Process(self.regkey)
    self.assertTrue(generator)
    entries = list(generator)

    line = (u'[\\Microsoft\\Some Windows\\InterestingApp\\MRU] MRUList: acb '
            'a: Some random text here b: [DATA TYPE BINARY] c: C:/looks_leg'
            'it.exe')

    self.assertEquals(len(entries), 1)
    self.assertEquals(entries[0].timestamp, 1346145829002031)
    msg, _ = eventdata.GetMessageStrings(entries[0])
    eventdata.GetFormatter(entries[0])
    self.assertEquals(msg, line)


if __name__ == '__main__':
  unittest.main()
