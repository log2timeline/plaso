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
"""Tests for the browser_search analysis plugin."""

import os
import unittest

from plaso.analysis import chrome_extension
from plaso.analysis import test_lib
from plaso.lib import event
from plaso.lib import queue

# We are accessing quite a lot of protected members in this test file.
# Suppressing that message test file wide.
# pylint: disable=protected-access


class AnalyzeChromeExtensionTestPlugin(
    chrome_extension.AnalyzeChromeExtensionPlugin):
  """Chrome extention analysis plugin used for testing."""

  NAME = 'chrome_extension_test'

  _TEST_DATA_PATH = os.path.join(
      os.getcwd(), u'test_data', u'chrome_extensions')

  def _GetChromeWebStorePage(self, extension_id):
    """Retrieves the page for the extension from the Chrome store test data.

    Args:
      extension_id: string containing the extension identifier.
    """
    chrome_web_store_file = os.path.join(self._TEST_DATA_PATH, extension_id)
    if not os.path.exists(chrome_web_store_file):
      return

    return open(chrome_web_store_file, 'rb')


class ChromeExtensionTest(test_lib.AnalysisPluginTestCase):
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

  def _CreateTestEventObject(self, path):
    """Create a test event object with a particular path."""
    event_object = event.EventObject()
    event_object.data_type = 'fs:stat'
    event_object.timestamp = 12345
    event_object.timestamp_desc = u'Some stuff'
    event_object.filename = path

    return event_object

  def testSeparator(self):
    """Test the separator detection."""
    pre_obj = event.PreprocessObject()
    analysis_plugin = chrome_extension.AnalyzeChromeExtensionPlugin(
        pre_obj, None, None)

    analysis_plugin._sep = u'/'
    for path in self.MAC_PATHS:
      self.assertEquals(analysis_plugin._GetSeparator(path), u'/')

    analysis_plugin._sep = u'\\'
    for path in self.WIN_PATHS:
      self.assertEquals(analysis_plugin._GetSeparator(path), u'\\')

  def testMacAnalyzerPlugin(self):
    """Test the plugin against mock events."""
    incoming_queue = queue.SingleThreadedQueue()
    outgoing_queue = queue.SingleThreadedQueue()
    pre_obj = event.PreprocessObject()

    # Fill in the user section
    pre_obj.users = self.MAC_USERS

    # Initialize plugin.
    analysis_plugin = AnalyzeChromeExtensionTestPlugin(
        pre_obj, incoming_queue, outgoing_queue)

    # Test the user creation.
    user_paths = analysis_plugin._user_paths
    self.assertEquals(
        set(user_paths.keys()), set([u'frank', u'dude', u'hans', u'root']))
    self.assertEquals(user_paths[u'frank'], u'/users/frank')
    self.assertEquals(user_paths[u'dude'], u'/users/dude')
    self.assertEquals(user_paths[u'hans'], u'/users/hans')
    self.assertEquals(user_paths[u'root'], u'/var/root')

    # Fill the incoming queue with events.
    test_queue_producer = queue.AnalysisPluginProducer(incoming_queue)
    test_queue_producer.ProduceEventObjects([
        self._CreateTestEventObject(path) for path in self.MAC_PATHS])
    test_queue_producer.SignalEndOfInput()

    # Run the analysis plugin.
    analysis_plugin.RunPlugin()

    outgoing_queue.SignalEndOfInput()
    test_analysis_plugin_consumer = test_lib.TestAnalysisPluginConsumer(
        outgoing_queue)
    test_analysis_plugin_consumer.ConsumeAnalysisReports()

    self.assertEquals(
        test_analysis_plugin_consumer.number_of_analysis_reports, 1)

    analysis_report = test_analysis_plugin_consumer.analysis_reports[0]

    # Test the username detection.
    self.assertEquals(analysis_plugin._GetUserNameFromPath(
        self.MAC_PATHS[0]), u'dude')
    self.assertEquals(analysis_plugin._GetUserNameFromPath(
        self.MAC_PATHS[4]), u'hans')

    self.assertEquals(analysis_plugin._sep, u'/')

    # Due to the behavior of the join one additional empty string at the end
    # is needed to create the last empty line.
    expected_text = u'\n'.join([
        u' == USER: dude ==',
        u'  Google Drive [apdfllckaahabafndbhieahigkjlhalf]',
        u'',
        u' == USER: frank ==',
        u'  Gmail [pjkljhegncpnkpknbcohdijeoejaedia]',
        u'',
        u''])

    self.assertEquals(analysis_report.text, expected_text)
    self.assertEquals(analysis_report.plugin_name, 'chrome_extension_test')

    expected_keys = set([u'frank', u'dude'])
    self.assertEquals(set(analysis_report.report_dict.keys()), expected_keys)

  def testWinAnalyzePlugin(self):
    """Test the plugin against mock events."""
    incoming_queue = queue.SingleThreadedQueue()
    outgoing_queue = queue.SingleThreadedQueue()
    pre_obj = event.PreprocessObject()

    # Fill in the user section
    pre_obj.users = self.WIN_USERS

    # Initialize plugin.
    analysis_plugin = AnalyzeChromeExtensionTestPlugin(
        pre_obj, incoming_queue, outgoing_queue)

    # Test the user creation.
    user_paths = analysis_plugin._user_paths
    self.assertEquals(set(user_paths.keys()), set([u'frank', u'dude']))
    self.assertEquals(user_paths[u'frank'], u'/users/frank')
    self.assertEquals(user_paths[u'dude'], u'/users/dude')

    # Fill the incoming queue with events.
    test_queue_producer = queue.AnalysisPluginProducer(incoming_queue)
    test_queue_producer.ProduceEventObjects([
        self._CreateTestEventObject(path) for path in self.WIN_PATHS])
    test_queue_producer.SignalEndOfInput()

    # Run the analysis plugin.
    analysis_plugin.RunPlugin()

    outgoing_queue.SignalEndOfInput()
    test_analysis_plugin_consumer = test_lib.TestAnalysisPluginConsumer(
        outgoing_queue)
    test_analysis_plugin_consumer.ConsumeAnalysisReports()

    self.assertEquals(
        test_analysis_plugin_consumer.number_of_analysis_reports, 1)

    analysis_report = test_analysis_plugin_consumer.analysis_reports[0]

    # Test the username detection.
    self.assertEquals(analysis_plugin._GetUserNameFromPath(
        self.WIN_PATHS[0]), u'dude')
    self.assertEquals(analysis_plugin._GetUserNameFromPath(
        self.WIN_PATHS[2]), u'frank')

    self.assertEquals(analysis_plugin._sep, u'\\')

    # Due to the behavior of the join one additional empty string at the end
    # is needed to create the last empty line.
    expected_text = u'\n'.join([
        u' == USER: dude ==',
        u'  Google Keep - notes and lists [hmjkmjkepdijhoojdojkdfohbdgmmhki]',
        u'',
        u' == USER: frank ==',
        u'  Google Play Music [icppfcnhkcmnfdhfhphakoifcfokfdhg]',
        u'  YouTube [blpcfgokakmgnkcojhhkbfbldkacnbeo]',
        u'',
        u''])

    self.assertEquals(analysis_report.text, expected_text)
    self.assertEquals(analysis_report.plugin_name, 'chrome_extension_test')

    expected_keys = set([u'frank', u'dude'])
    self.assertEquals(set(analysis_report.report_dict.keys()), expected_keys)


if __name__ == '__main__':
  unittest.main()
