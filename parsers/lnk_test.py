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
"""Tests for the Windows Shortcut (LNK) parser."""
import os
import unittest

from plaso.lib import preprocess
from plaso.parsers import lnk


class WinLnkParserTest(unittest.TestCase):
  """Tests for the Windows Shortcut (LNK) parser."""

  def setUp(self):
    """Sets up the needed objects used throughout the test."""
    pre_obj = preprocess.PlasoPreprocess()
    self.base_path = os.path.join('plaso/test_data')
    self.parser_obj = lnk.WinLnkParser(pre_obj)

  def testWinLnkParserFile(self):
    """Read a LNK file and make few tests."""
    lnk_path = os.path.join(self.base_path, 'example.lnk')

    events = []
    # Creation time:     Jul 13, 2009 23:29:02.849131000 UTC
    # Modification time: Jul 14, 2009 01:39:18.220000000 UTC
    # Last Access time:  Jul 13, 2009 23:29:02.849131000 UTC

    # date -u -d"Jul 13, 2009 23:29:02.849131000" +"%s.%N"
    # date -u -d"Jul 14, 2009 01:39:18.220000000" +"%s.%N"
    event_dict = {
        'Creation Time': (1247527742 * 1000000) + int(849131000 / 1000),
        'Modification Time': (1247535558 * 1000000) + int(220000000 / 1000),
        'Last Access Time': (1247527742 * 1000000) + int(849131000 / 1000),
    }
    with open(lnk_path, 'rb') as fh:
      events = list(self.parser_obj.Parse(fh))

    self.assertEquals(len(events), 3)

    for event in events:
      self.assertEquals(
          event.timestamp, event_dict.get(event.timestamp_desc, 0))

    times = [x.timestamp for x in events]
    times_compare = [x for _, x in event_dict.items()]
    self.assertEquals(sorted(times), sorted(times_compare))

if __name__ == '__main__':
  unittest.main()
