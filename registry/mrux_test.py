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
"""This file contains a test for MRUx registry parsing in Plaso."""
import unittest

from plaso.registry import mrux
from plaso.registry import test_lib


class TestMRURegistry(unittest.TestCase):
  """The unit test for MRU registry parsing."""

  def setUp(self):
    """Sets up the needed objects used throughout the test."""
    values = []
    # The order is: 201
    values.append(test_lib.TestRegValue(
        'MRUListEx', '\x02\x00\x00\x00\x00\x00\x00\x00\x01\x00\x00\x00',
        3, 123))
    values.append(test_lib.TestRegValue(
        '0', 'Some random text here'.encode('utf_16_le'), 1, 1892))
    values.append(test_lib.TestRegValue(
        '1', 'c:/evil.exe'.encode('utf_16_le'), 3, 612))
    values.append(test_lib.TestRegValue(
        '2', 'C:/looks_legit.exe'.encode('utf_16_le'), 1, 1001))

    self.regkey = test_lib.TestRegKey(
        '\\Microsoft\\Some Windows\\InterestingApp\\MRUlist', 1346145829002031,
        values, 1456)

  def testWinVer(self):
    plugin = mrux.MRUexPlugin(None)
    entries = list(plugin.Process(self.regkey))

    line0 = ('[\\Microsoft\\Some Windows\\InterestingApp\\MRUlist] MRUListEx '
             'Entry 0 (nr. 2): Some random text here')
    line1 = ('[\\Microsoft\\Some Windows\\InterestingApp\\MRUlist] MRUListEx '
             'Entry 1 (nr. 3): c:/evil.exe')
    line2 = ('[\\Microsoft\\Some Windows\\InterestingApp\\MRUlist] MRUListEx '
             'Entry 2 (nr. 1): C:/looks_legit.exe')

    self.assertEquals(len(entries), 3)
    self.assertEquals(entries[0].timestamp, 1346145829002031)
    self.assertEquals(entries[1].timestamp, 0)
    self.assertEquals(entries[2].timestamp, 0)
    self.assertEquals(entries[0].description_long, line2)
    self.assertEquals(entries[1].description_long, line0)
    self.assertEquals(entries[2].description_long, line1)


if __name__ == '__main__':
  unittest.main()
