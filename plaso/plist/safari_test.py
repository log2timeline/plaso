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
"""This file contains a test for the Safari History plist parser."""
import os
import unittest

from plaso.lib import preprocess
from plaso.lib import putils

from plaso.parsers import plist
from plaso.plist import safari


class TestSafariPlugin(unittest.TestCase):
  """The unit test for Safari history parser."""

  def setUp(self):
    """Sets up the needed objects used throughout the test."""
    self.plugin = safari.SafariHistoryPlugin(None)
    parser = plist.PlistParser(preprocess.PlasoPreprocess())

    self.plist_binary = os.path.join('test_data', 'History.plist')

    with putils.OpenOSFile(self.plist_binary) as fd:
      self.top_level_object = parser.GetTopLevel(fd)

  def testGetEntries(self):
    """Ensure that the Safari history file is parsed correctly."""
    name = 'History.plist'

    events = list(self.plugin.Process(name, self.top_level_object))

    # 18 entries in timeline.
    self.assertEquals(len(events), 18)

    # Mon Jul  8 17:31:00 UTC 2013.
    self.assertEquals(events[10].timestamp, 1373304660000000)
    self.assertEquals(events[8].url, 'http://netverslun.sci-mx.is/aminosyrur')


if __name__ == '__main__':
  unittest.main()
