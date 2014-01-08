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
"""Tests for the Windows Registry file parser."""

import unittest

from plaso.lib import preprocess
from plaso.parsers import test_lib
from plaso.parsers import winreg


class WinRegTest(test_lib.ParserTestCase):
  """Tests for the Windows Registry file parser."""

  def setUp(self):
    """Sets up the needed objects used throughout the test."""
    pre_obj = preprocess.PlasoPreprocess()
    pre_obj.current_control_set = 'ControlSet001'
    self._parser = winreg.WinRegistryParser(pre_obj)

  def _GetPlugins(self, events):
    """Return a dict with a plugin count given an event generator."""
    plugins = {}
    for event_object in events:
      if event_object.plugin in plugins:
        plugins[event_object.plugin] += 1
      else:
        plugins[event_object.plugin] = 1

    return plugins

  def testNtuserParsing(self):
    """Parse a NTUSER.dat file and check few items."""
    test_file = self._GetTestFilePath(['NTUSER.DAT'])
    events = self._ParseFile(self._parser, test_file)

    # pylint: disable-msg=W0212
    self.assertEquals(self._parser._registry_type, 'NTUSER')

    plugins = self._GetPlugins(events)

    self.assertTrue('winreg_userassist_2' in plugins)
    self.assertTrue('winreg_userassist_3' in plugins)

    self.assertEquals(plugins['winreg_userassist_2'], 1)
    self.assertEquals(plugins['winreg_userassist_3'], 15)

  def testSystemParsing(self):
    """Parse a SYSTEM hive an run few tests."""
    test_file = self._GetTestFilePath(['SYSTEM'])
    events = self._ParseFile(self._parser, test_file)

    # pylint: disable-msg=W0212
    self.assertEquals(self._parser._registry_type, 'SYSTEM')

    plugins = self._GetPlugins(events)

    # Check the existence of few known plugins, see if they
    # are being properly picked up and are parsed.
    self.assertTrue('winreg_usbstor' in plugins)
    self.assertTrue('winreg_boot_execute' in plugins)
    self.assertTrue('winreg_services' in plugins)

    self.assertEquals(plugins.get('winreg_usbstor', 0), 3)
    self.assertEquals(plugins.get('winreg_boot_execute', 0), 2)
    self.assertEquals(plugins.get('winreg_services', 0), 831)


if __name__ == '__main__':
  unittest.main()
