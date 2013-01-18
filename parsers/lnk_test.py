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

from plaso.lib import eventdata
from plaso.lib import preprocess
from plaso.parsers import lnk


class WinLnkParserTest(unittest.TestCase):
  """Tests for the Windows Shortcut (LNK) parser."""

  def setUp(self):
    """Sets up the needed objects used throughout the test."""
    pre_obj = preprocess.PlasoPreprocess()
    self.test_parser = lnk.WinLnkParser(pre_obj)

  def testWinLnkParserFile(self):
    """Read a LNK file and make few tests."""
    lnk_path = os.path.join('plaso', 'test_data', 'example.lnk')

    event_container = None
    with open(lnk_path, 'rb') as fh:
      event_container = self.test_parser.Parse(fh)

    # Link information:
    # 	Creation time			: Jul 13, 2009 23:29:02.849131000 UTC
    # 	Modification time		: Jul 14, 2009 01:39:18.220000000 UTC
    # 	Access time			: Jul 13, 2009 23:29:02.849131000 UTC
    # 	Description			: @%windir%\system32\migwiz\wet.dll,-590
    # 	Relative path			: .\migwiz\migwiz.exe
    # 	Working directory		: %windir%\system32\migwiz
    # 	Icon location			: %windir%\system32\migwiz\migwiz.exe
    # 	Environment variables location	: %windir%\system32\migwiz\migwiz.exe

    self.assertEquals(len(event_container), 3)

    expected_string = u'@%windir%\system32\migwiz\wet.dll,-590'
    self.assertEquals(event_container.description, expected_string)

    expected_string = u'.\migwiz\migwiz.exe'
    self.assertEquals(event_container.relative_path, expected_string)

    expected_string = u'%windir%\system32\migwiz'
    self.assertEquals(event_container.working_directory, expected_string)

    expected_string = u'%windir%\system32\migwiz\migwiz.exe'
    self.assertEquals(event_container.icon_location, expected_string)
    self.assertEquals(event_container.env_var_location, expected_string)

    # date -u -d"Jul 13, 2009 23:29:02.849131000" +"%s.%N"
    event_object = event_container.events[0]
    self.assertEquals(event_object.timestamp_desc,
                      eventdata.EventTimestamp.ACCESS_TIME)
    self.assertEquals(event_object.timestamp,
                      (1247527742 * 1000000) + int(849131000 / 1000))

    # date -u -d"Jul 13, 2009 23:29:02.849131000" +"%s.%N"
    event_object = event_container.events[1]
    self.assertEquals(event_object.timestamp_desc,
                      eventdata.EventTimestamp.CREATION_TIME)
    self.assertEquals(event_object.timestamp,
                      (1247527742 * 1000000) + int(849131000 / 1000))

    # date -u -d"Jul 14, 2009 01:39:18.220000000" +"%s.%N"
    event_object = event_container.events[2]
    self.assertEquals(event_object.timestamp_desc,
                      eventdata.EventTimestamp.MODIFICATION_TIME)
    self.assertEquals(event_object.timestamp,
                      (1247535558 * 1000000) + int(220000000 / 1000))

if __name__ == '__main__':
  unittest.main()
