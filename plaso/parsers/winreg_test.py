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
"""This file contains the unit tests for Windows registry parsing in Plaso."""
import os
import unittest

from plaso.lib import preprocess
from plaso.parsers import winreg
from plaso.pvfs import utils


class WinRegTest(unittest.TestCase):
  """The unit test for winreg parser."""

  def setUp(self):
    """Sets up the needed objects used throughout the test."""
    self.base_path = 'test_data'
    self.pre = preprocess.PlasoPreprocess()
    self.pre.current_control_set = 'ControlSet001'

  def testNtuserParsing(self):
    """Parse a NTUSER.dat file and check few items."""
    event_gen = self._ParseRegistryFile('NTUSER.DAT', 'NTUSER')
    plugins = self._GetPlugins(event_gen)

    self.assertTrue('winreg_userassist_2' in plugins)
    self.assertTrue('winreg_userassist_3' in plugins)

    self.assertEquals(plugins['winreg_userassist_2'], 1)
    self.assertEquals(plugins['winreg_userassist_3'], 15)

  def _GetPlugins(self, event_gen):
    """Return a dict with a plugin count given an event generator."""
    plugins = {}
    for event_object in event_gen:
      if event_object.plugin in plugins:
        plugins[event_object.plugin] += 1
      else:
        plugins[event_object.plugin] = 1

    return plugins

  def testSystemParsing(self):
    """Parse a SYSTEM hive an run few tests."""
    event_gen = self._ParseRegistryFile('SYSTEM', 'SYSTEM')

    plugins = self._GetPlugins(event_gen)

    # Check the existence of few known plugins, see if they
    # are being properly picked up and are parsed.
    self.assertTrue('winreg_usbstor' in plugins)
    self.assertTrue('winreg_boot_execute' in plugins)
    self.assertTrue('winreg_services' in plugins)

    self.assertEquals(plugins.get('winreg_usbstor', 0), 3)
    self.assertEquals(plugins.get('winreg_boot_execute', 0), 2)
    self.assertEquals(plugins.get('winreg_services', 0), 831)


  def _ParseRegistryFile(self, filename, correct_type):
    """Open up a filehandle and yield all event objects."""
    file_path = os.path.join(self.base_path, filename)
    fh = utils.OpenOSFile(file_path)
    parser = winreg.WinRegistryParser(self.pre, None)
    for event_object in parser.Parse(fh):
      yield event_object
    fh.close()
    # pylint: disable-msg=W0212
    self.assertEquals(parser._registry_type, correct_type)


if __name__ == '__main__':
  unittest.main()
