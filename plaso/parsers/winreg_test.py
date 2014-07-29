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

from plaso.lib import event
from plaso.parsers import test_lib
from plaso.parsers import winreg


class WinRegTest(test_lib.ParserTestCase):
  """Tests for the Windows Registry file parser."""

  def setUp(self):
    """Sets up the needed objects used throughout the test."""
    pre_obj = event.PreprocessObject()
    pre_obj.current_control_set = 'ControlSet001'
    self._parser = winreg.WinRegistryParser(pre_obj)

  def _GetPlugins(self, event_generator):
    """Return a dict with a plugin count given an event generator."""
    plugins = {}
    for event_object in event_generator:
      if event_object.plugin in plugins:
        plugins[event_object.plugin] += 1
      else:
        plugins[event_object.plugin] = 1

    return plugins

  def testNtuserParsing(self):
    """Parse a NTUSER.dat file and check few items."""
    test_file = self._GetTestFilePath(['NTUSER.DAT'])
    event_generator = self._ParseFile(self._parser, test_file)

    plugins = self._GetPlugins(event_generator)

    # The _registry_type member is created dynamically by invoking
    # the _GetPlugins function.
    registry_type = getattr(self._parser, '_registry_type', '')
    self.assertEquals(registry_type, 'NTUSER')

    self.assertTrue('winreg_userassist' in plugins)

    # TODO: Delete this once RegAlert is completely removed
    # self.assertEquals(plugins['winreg_userassist'], 16)
    self.assertEquals(plugins['winreg_userassist'], 14)

  def testSystemParsing(self):
    """Parse a SYSTEM hive an run few tests."""
    test_file = self._GetTestFilePath(['SYSTEM'])
    event_generator = self._ParseFile(self._parser, test_file)

    plugins = self._GetPlugins(event_generator)

    # The _registry_type member is created dynamically by invoking
    # the _GetPlugins function.
    registry_type = getattr(self._parser, '_registry_type', '')
    self.assertEquals(registry_type, 'SYSTEM')

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
