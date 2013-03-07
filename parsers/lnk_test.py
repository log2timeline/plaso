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

from plaso.formatters import lnk
from plaso.lib import eventdata
from plaso.lib import preprocess
from plaso.parsers import lnk


class WinLnkParserTest(unittest.TestCase):
  """Tests for the Windows Shortcut (LNK) parser."""

  def setUp(self):
    """Sets up the needed objects used throughout the test."""
    pre_obj = preprocess.PlasoPreprocess()
    self.test_parser = lnk.WinLnkParser(pre_obj)
    self.maxDiff = None

  def testParseFile(self):
    """Read a LNK file and run a few tests."""
    test_file = os.path.join('test_data', 'example.lnk')

    events = None
    with open(test_file, 'rb') as file_object:
      events = list(self.test_parser.Parse(file_object))

    # Link information:
    # 	Creation time			: Jul 13, 2009 23:29:02.849131000 UTC
    # 	Modification time		: Jul 14, 2009 01:39:18.220000000 UTC
    # 	Access time			: Jul 13, 2009 23:29:02.849131000 UTC
    # 	Description			: @%windir%\system32\migwiz\wet.dll,-590
    # 	Relative path			: .\migwiz\migwiz.exe
    # 	Working directory		: %windir%\system32\migwiz
    # 	Icon location			: %windir%\system32\migwiz\migwiz.exe
    # 	Environment variables location	: %windir%\system32\migwiz\migwiz.exe

    self.assertEquals(len(events), 3)

    # The Last Accessed timestamp.
    event_object = events[0]

    expected_string = u'@%windir%\system32\migwiz\wet.dll,-590'
    self.assertEquals(event_object.description, expected_string)

    expected_string = u'.\migwiz\migwiz.exe'
    self.assertEquals(event_object.relative_path, expected_string)

    expected_string = u'%windir%\system32\migwiz'
    self.assertEquals(event_object.working_directory, expected_string)

    expected_string = u'%windir%\system32\migwiz\migwiz.exe'
    self.assertEquals(event_object.icon_location, expected_string)
    self.assertEquals(event_object.env_var_location, expected_string)

    # date -u -d"Jul 13, 2009 23:29:02.849131000" +"%s.%N"
    self.assertEquals(event_object.timestamp_desc,
                      eventdata.EventTimestamp.ACCESS_TIME)
    self.assertEquals(event_object.timestamp,
                      (1247527742 * 1000000) + int(849131000 / 1000))

    # date -u -d"Jul 13, 2009 23:29:02.849131000" +"%s.%N"
    event_object = events[1]
    self.assertEquals(event_object.timestamp_desc,
                      eventdata.EventTimestamp.CREATION_TIME)
    self.assertEquals(event_object.timestamp,
                      (1247527742 * 1000000) + int(849131000 / 1000))

    # date -u -d"Jul 14, 2009 01:39:18.220000000" +"%s.%N"
    event_object = events[2]
    self.assertEquals(event_object.timestamp_desc,
                      eventdata.EventTimestamp.MODIFICATION_TIME)
    self.assertEquals(event_object.timestamp,
                      (1247535558 * 1000000) + int(220000000 / 1000))

    # Test the event specific formatter.
    msg, msg_short = eventdata.EventFormatterManager.GetMessageStrings(
         event_object)

    expected_msg = (u'[@%windir%\\system32\\migwiz\\wet.dll,-590] '
                    u'File size: 544768 '
                    u'File attribute flags: 0x00000020 '
                    u'env location: %windir%\\system32\\migwiz\\migwiz.exe '
                    u'Relative path: .\\migwiz\\migwiz.exe '
                    u'Working dir: %windir%\\system32\\migwiz '
                    u'Icon location: %windir%\\system32\\migwiz\\migwiz.exe')

    self.assertEquals(msg, expected_msg)


if __name__ == '__main__':
  unittest.main()
