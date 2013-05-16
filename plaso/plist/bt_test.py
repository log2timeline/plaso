#!/usr/bin/python
# -*- coding: utf-8 -*-
# Copyright 2013 The Plaso Project Authors.
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
"""This file contains a test for the default plist parser."""

import os
import unittest

from plaso.lib import preprocess

from plaso.parsers import plist
from plaso.plist import bt


class TestBtPlugin(unittest.TestCase):
  """The unit test for default plist parser."""

  def setUp(self):
    """Sets up the needed objects used throughout the test."""
    self.plugin = bt.BtPlugin(None)
    parser = plist.PlistParser(preprocess.PlasoPreprocess())

    self.plist_binary = os.path.join('test_data', 'plist_binary')

    with open(self.plist_binary) as fd:
      self.top_level_object = parser.GetTopLevel(fd)

  def testGetEntries(self):
    """Ensure that the bluetooth plist file is parsed correctly."""
    name = 'com.apple.bluetooth.plist'

    timestamps = []
    paired = []
    for event in self.plugin.Process(name, self.top_level_object):
      timestamps.append(event.timestamp)
      if 'Paired' in event.desc:
        paired.append(event)

    # Ensure all 14 events and times from the plist are parsed correctly.
    self.assertEquals(len(timestamps), 14)
    correct_timestamps = frozenset([1351818797000000, 1351818797000000,
                                    1351819298000000, 1351818803000000,
                                    1301012201000000, 1341957900000000,
                                    1302199013000000, 1350666385000000,
                                    1350666391000000, 1341957896000000,
                                    1341957896000000, 1351827808000000,
                                    1345251268000000, 1345251192000000])
    self.assertTrue(correct_timestamps == set(timestamps))

    # Ensure two paired devices are matched.
    self.assertEquals(len(paired), 2)
    self.assertTrue('Paired:True Name:Apple Magic Trackpad 2' in [
        x.desc for x in paired])

if __name__ == '__main__':
  unittest.main()
