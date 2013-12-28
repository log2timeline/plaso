#!/usr/bin/python
# -*- coding: utf-8 -*-
#
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
from plaso.parsers.plist_plugins import bt
from plaso.pvfs import utils


class TestBtPlugin(unittest.TestCase):
  """The unit test for default plist parser."""

  def setUp(self):
    """Sets up the needed objects used throughout the test."""
    self.plugin = bt.BtPlugin(None)
    self._parser = plist.PlistParser(preprocess.PlasoPreprocess(), None)

  def testGetEntries(self):
    """Ensure that the bluetooth plist file is parsed correctly."""
    name = 'com.apple.bluetooth.plist'

    test_file = os.path.join('test_data', 'plist_binary')

    file_entry = utils.OpenOSFileEntry(test_file)
    top_level_object = self._parser.GetTopLevel(file_entry)

    timestamps = []
    paired = []
    for event in self.plugin.Process(name, top_level_object):
      timestamps.append(event.timestamp)
      if 'Paired' in event.desc:
        paired.append(event)

    # Ensure all 14 events and times from the plist are parsed correctly.
    self.assertEquals(len(timestamps), 14)

    correct_timestamps = frozenset([
        1341957896010535, 1341957896010535, 1350666385239661, 1350666391557044,
        1341957900020116, 1302199013524275, 1301012201414766, 1351818797324095,
        1351818797324095, 1351819298997672, 1351818803000000, 1351827808261762,
        1345251268370453, 1345251192528750])

    self.assertTrue(correct_timestamps == set(timestamps))

    # Ensure two paired devices are matched.
    self.assertEquals(len(paired), 2)
    self.assertTrue('Paired:True Name:Apple Magic Trackpad 2' in [
        x.desc for x in paired])


if __name__ == '__main__':
  unittest.main()
