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
"""Tests for the browser_search analysis plugin."""
import unittest

from plaso.analysis import chrome_extension
from plaso.lib import analysis_interface
from plaso.lib import event
from plaso.lib import preprocess
from plaso.lib import queue

import pytz
# We are accessing quite a lot of protected members in this test file.
# Suppressing that message test file wide.
# pylint: disable-msg=protected-access


class ChromeExtensionTest(unittest.TestCase):
  """Tests for the chrome extension analysis plugin."""

  # Few config options here.
  MAC_PATHS = [
      '/Users/dude/Libary/Application Data/Google/Chrome/Default/Extensions',
      ('/Users/dude/Libary/Application Data/Google/Chrome/Default/Extensions/'
       'apdfllckaahabafndbhieahigkjlhalf'),
      '/private/var/log/system.log',
      '/Users/frank/Library/Application Data/Google/Chrome/Default',
      '/Users/hans/Library/Application Data/Google/Chrome/Default',
      ('/Users/frank/Library/Application Data/Google/Chrome/Default/'
       'Extensions/pjkljhegncpnkpknbcohdijeoejaedia'),
      '/Users/frank/Library/Application Data/Google/Chrome/Default/Extensions',]

  WIN_PATHS = [
      'C:\\Users\\Dude\\SomeFolder\\Chrome\\Default\\Extensions',
      ('C:\\Users\\Dude\\SomeNoneStandardFolder\\Chrome\\Default\\Extensions\\'
       'hmjkmjkepdijhoojdojkdfohbdgmmhki'),
      ('\\Users\\frank\\AppData\\Local\\Google\\Chrome\\Extensions\\'
       'blpcfgokakmgnkcojhhkbfbldkacnbeo'),
      '\\Users\\frank\\AppData\\Local\\Google\\Chrome\\Extensions',
      ('\\Users\\frank\\AppData\\Local\\Google\\Chrome\\Extensions\\'
       'icppfcnhkcmnfdhfhphakoifcfokfdhg'),
      'C:\\Windows\\System32',
      '\\Stuff/with path separator\\Folder']

  MAC_USERS = [
      {u'name': u'root', u'path': u'/var/root', u'sid': u'0'},
      {u'name': u'frank', u'path': u'/Users/frank', u'sid': u'4052'},
      {u'name': u'hans', u'path': u'/Users/hans', u'sid': u'4352'},
      {u'name': u'dude', u'path': u'/Users/dude', u'sid': u'1123'}]

  WIN_USERS = [
      {u'name': u'dude', u'path': u'C:\\Users\\dude', u'sid': u'S-1'},
      {u'name': u'frank', u'path': u'C:\\Users\\frank', u'sid': u'S-2'}]

  def setUp(self):
    """Sets up the needed objects used throughout the test."""
    # Show full diff results, part of TestCase so does not follow our naming
    # conventions.
    self.maxDiff = None

  def testSeparator(self):
    """Test the separator detection."""
    pre_obj = preprocess.PlasoPreprocess()
    analysis_plugin = chrome_extension.AnalyzeChromeExtensionPlugin(
        pre_obj, None, None)

    analysis_plugin._sep = '/'
    for path in self.MAC_PATHS:
      self.assertEquals(analysis_plugin._GetSeparator(path), '/')

    analysis_plugin._sep = '\\'
    for path in self.WIN_PATHS:
      self.assertEquals(analysis_plugin._GetSeparator(path), '\\')

  def _CreateEvent(self, path):
    """Create a mock event with a particular path."""
    event_object = event.EventObject()
    event_object.data_type = 'fs:stat'
    event_object.timestamp = 12345
    event_object.timestamp_desc = 'Some stuff'
    event_object.filename = path

    return event_object

  def testMacAnalyzerPlugin(self):
    """Test the plugin against mock events."""
    # Create queues and other necessary objects.
    incoming_queue = queue.SingleThreadedQueue()
    outgoing_queue = queue.SingleThreadedQueue()
    pre_obj = preprocess.PlasoPreprocess()
    pre_obj.zone = pytz.utc

    # Fill in the user section
    pre_obj.users = self.MAC_USERS

    # Initialize plugin.
    analysis_plugin = chrome_extension.AnalyzeChromeExtensionPlugin(
        pre_obj, incoming_queue, outgoing_queue)

    # Test the user creation.
    user_paths = analysis_plugin._user_paths
    self.assertEquals(
        set(user_paths.keys()), set(['frank', 'dude', 'hans', 'root']))
    self.assertEquals(user_paths['frank'], '/users/frank')
    self.assertEquals(user_paths['dude'], '/users/dude')
    self.assertEquals(user_paths['hans'], '/users/hans')
    self.assertEquals(user_paths['root'], '/var/root')

    # Fill the incoming queue with events.
    for path in self.MAC_PATHS:
      event_object = self._CreateEvent(path)
      incoming_queue.AddEvent(event_object.ToJson())
    incoming_queue.Close()

    # Run the analysis plugin.
    analysis_plugin.RunPlugin()

    # Get the report out.
    outgoing_queue.Close()
    output = []
    for item in outgoing_queue.PopItems():
      output.append(item)

    # Test the username detection.
    self.assertEquals(analysis_plugin._GetUserNameFromPath(
        self.MAC_PATHS[0]), 'dude')
    self.assertEquals(analysis_plugin._GetUserNameFromPath(
        self.MAC_PATHS[4]), 'hans')

    # There is only a report returned back.
    self.assertEquals(len(output), 1)

    self.assertEquals(analysis_plugin._sep, '/')

    report_string = output[0]
    self.assertEquals(
        report_string[0], analysis_interface.MESSAGE_STRUCT.build(
            analysis_interface.MESSAGE_REPORT))

    report = analysis_interface.AnalysisReport()
    report.FromProtoString(report_string[1:])

    expected_text = """\
 == USER: dude ==
  Google Drive [apdfllckaahabafndbhieahigkjlhalf]

 == USER: frank ==
  Gmail [pjkljhegncpnkpknbcohdijeoejaedia]

"""
    self.assertEquals(expected_text, report.text)
    self.assertEquals(report.plugin_name, 'chrome_extension')

    self.assertEquals(
        set(report.report_dict.keys()), set([u'frank', u'dude']))

  def testWinAnalyzePlugin(self):
    """Test the plugin against mock events."""
    # Create queues and other necessary objects.
    incoming_queue = queue.SingleThreadedQueue()
    outgoing_queue = queue.SingleThreadedQueue()
    pre_obj = preprocess.PlasoPreprocess()
    pre_obj.zone = pytz.utc

    # Fill in the user section
    pre_obj.users = self.WIN_USERS

    # Initialize plugin.
    analysis_plugin = chrome_extension.AnalyzeChromeExtensionPlugin(
        pre_obj, incoming_queue, outgoing_queue)

    # Test the user creation.
    user_paths = analysis_plugin._user_paths
    self.assertEquals(set(user_paths.keys()), set(['frank', 'dude']))
    self.assertEquals(user_paths['frank'], '/users/frank')
    self.assertEquals(user_paths['dude'], '/users/dude')

    # Fill the incoming queue with events.
    for path in self.WIN_PATHS:
      event_object = self._CreateEvent(path)
      incoming_queue.AddEvent(event_object.ToJson())
    incoming_queue.Close()

    # Run the analysis plugin.
    analysis_plugin.RunPlugin()

    # Get the report out.
    outgoing_queue.Close()
    output = []
    for item in outgoing_queue.PopItems():
      output.append(item)

    # Test the username detection.
    self.assertEquals(analysis_plugin._GetUserNameFromPath(
        self.WIN_PATHS[0]), 'dude')
    self.assertEquals(analysis_plugin._GetUserNameFromPath(
        self.WIN_PATHS[2]), 'frank')

    # There is only a report returned back.
    self.assertEquals(len(output), 1)

    self.assertEquals(analysis_plugin._sep, '\\')

    report_string = output[0]
    self.assertEquals(
        report_string[0], analysis_interface.MESSAGE_STRUCT.build(
            analysis_interface.MESSAGE_REPORT))

    report = analysis_interface.AnalysisReport()
    report.FromProtoString(report_string[1:])

    expected_text = """\
 == USER: dude ==
  Google Keep [hmjkmjkepdijhoojdojkdfohbdgmmhki]

 == USER: frank ==
  Google Play Music [icppfcnhkcmnfdhfhphakoifcfokfdhg]
  YouTube [blpcfgokakmgnkcojhhkbfbldkacnbeo]

"""

    self.assertEquals(expected_text, report.text)
    self.assertEquals(report.plugin_name, 'chrome_extension')

    self.assertEquals(
        set(report.report_dict.keys()), set([u'frank', u'dude']))


if __name__ == '__main__':
  unittest.main()
