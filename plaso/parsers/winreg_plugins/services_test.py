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
"""This file contains tests for Services Windows Registry plugin."""

import unittest

# pylint: disable=unused-import
from plaso.formatters import winreg as winreg_formatter
from plaso.lib import timelib_test
from plaso.parsers.winreg_plugins import services
from plaso.parsers.winreg_plugins import test_lib
from plaso.winreg import test_lib as winreg_test_lib


class ServicesRegistryPluginTest(test_lib.RegistryPluginTestCase):
  """The unit test for Services Windows Registry plugin."""

  def setUp(self):
    """Sets up the needed objects used throughout the test."""
    self._plugin = services.ServicesPlugin()

  def testProcess(self):
    """Tests the Process function on a virtual key."""
    key_path = u'\\ControlSet001\\services\\TestDriver'

    values = []
    values.append(winreg_test_lib.TestRegValue(
        'Type', '\x02\x00\x00\x00', 4, 123))
    values.append(winreg_test_lib.TestRegValue(
        'Start', '\x02\x00\x00\x00', 4, 127))
    values.append(winreg_test_lib.TestRegValue(
        'ErrorControl', '\x01\x00\x00\x00', 4, 131))
    values.append(winreg_test_lib.TestRegValue(
        'Group', 'Pnp Filter'.encode('utf_16_le'), 1, 140))
    values.append(winreg_test_lib.TestRegValue(
        'DisplayName', 'Test Driver'.encode('utf_16_le'), 1, 160))
    values.append(winreg_test_lib.TestRegValue(
        'DriverPackageId',
        'testdriver.inf_x86_neutral_dd39b6b0a45226c4'.encode('utf_16_le'), 1,
        180))
    values.append(winreg_test_lib.TestRegValue(
        'ImagePath', 'C:\\Dell\\testdriver.sys'.encode('utf_16_le'), 1, 200))

    timestamp = timelib_test.CopyStringToTimestamp(
        '2012-08-28 09:23:49.002031')
    winreg_key = winreg_test_lib.TestRegKey(
        key_path, timestamp, values, 1456)

    event_queue_consumer = self._ParseKeyWithPlugin(self._plugin, winreg_key)
    event_objects = self._GetEventObjectsFromQueue(event_queue_consumer)

    self.assertEquals(len(event_objects), 1)

    event_object = event_objects[0]

    # This should just be the plugin name, as we're invoking it directly,
    # and not through the parser.
    self.assertEquals(event_object.parser, self._plugin.plugin_name)

    expected_timestamp = timelib_test.CopyStringToTimestamp(
        '2012-08-28 09:23:49.002031')
    self.assertEquals(event_object.timestamp, expected_timestamp)

    expected_msg = (
        u'[{0:s}] '
        u'DisplayName: Test Driver '
        u'DriverPackageId: testdriver.inf_x86_neutral_dd39b6b0a45226c4 '
        u'ErrorControl: Normal (1) '
        u'Group: Pnp Filter '
        u'ImagePath: C:\\Dell\\testdriver.sys '
        u'Start: Auto Start (2) '
        u'Type: File System Driver (0x2)').format(key_path)
    expected_msg_short = (
        u'[{0:s}] '
        u'DisplayName: Test Driver '
        u'DriverPackageId...').format(key_path)

    self._TestGetMessageStrings(event_object, expected_msg, expected_msg_short)

  def testProcessFile(self):
    """Tests the Process function on a key in a file."""
    test_file_entry = self._GetTestFileEntryFromPath(['SYSTEM'])
    key_path = u'\\ControlSet001\\services'
    winreg_key = self._GetKeyFromFileEntry(test_file_entry, key_path)

    event_objects = []

    # Select a few service subkeys to perform additional testing.
    bits_event_objects = None
    mc_task_manager_event_objects = None
    rdp_video_miniport_event_objects = None

    for winreg_subkey in winreg_key.GetSubkeys():
      event_queue_consumer = self._ParseKeyWithPlugin(
          self._plugin, winreg_subkey, file_entry=test_file_entry)
      sub_event_objects = self._GetEventObjectsFromQueue(event_queue_consumer)

      event_objects.extend(sub_event_objects)

      if winreg_subkey.name == 'BITS':
        bits_event_objects = sub_event_objects
      elif winreg_subkey.name == 'McTaskManager':
        mc_task_manager_event_objects = sub_event_objects
      elif winreg_subkey.name == 'RdpVideoMiniport':
        rdp_video_miniport_event_objects = sub_event_objects

    self.assertEquals(len(event_objects), 416)

    # Test the BITS subkey event objects.
    self.assertEquals(len(bits_event_objects), 1)

    event_object = bits_event_objects[0]

    self.assertEquals(event_object.pathspec, test_file_entry.path_spec)
    # This should just be the plugin name, as we're invoking it directly,
    # and not through the parser.
    self.assertEquals(event_object.parser, self._plugin.plugin_name)

    expected_timestamp = timelib_test.CopyStringToTimestamp(
        '2012-04-06 20:43:27.639075')
    self.assertEquals(event_object.timestamp, expected_timestamp)

    self._TestRegvalue(event_object, u'Type', 0x20)
    self._TestRegvalue(event_object, u'Start', 3)
    self._TestRegvalue(
        event_object, u'ServiceDll', u'%SystemRoot%\\System32\\qmgr.dll')

    # Test the McTaskManager subkey event objects.
    self.assertEquals(len(mc_task_manager_event_objects), 1)

    event_object = mc_task_manager_event_objects[0]

    expected_timestamp = timelib_test.CopyStringToTimestamp(
        '2011-09-16 20:49:16.877415')
    self.assertEquals(event_object.timestamp, expected_timestamp)

    self._TestRegvalue(event_object, u'DisplayName', u'McAfee Task Manager')
    self._TestRegvalue(event_object, u'Type', 0x10)

    # Test the RdpVideoMiniport subkey event objects.
    self.assertEquals(len(rdp_video_miniport_event_objects), 1)

    event_object = rdp_video_miniport_event_objects[0]

    expected_timestamp = timelib_test.CopyStringToTimestamp(
        '2011-09-17 13:37:59.347157')
    self.assertEquals(event_object.timestamp, expected_timestamp)

    self._TestRegvalue(event_object, u'Start', 3)
    expected_value = u'System32\\drivers\\rdpvideominiport.sys'
    self._TestRegvalue(event_object, u'ImagePath', expected_value)


if __name__ == '__main__':
  unittest.main()
