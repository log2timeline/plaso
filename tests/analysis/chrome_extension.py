#!/usr/bin/python
# -*- coding: utf-8 -*-
"""Tests for the chrome extension analysis plugin."""

import os
import unittest

from plaso.analysis import chrome_extension
from plaso.containers import events
from plaso.engine import plaso_queue
from plaso.engine import single_process

from tests.analysis import test_lib

# We are accessing quite a lot of protected members in this test file.
# Suppressing that message test file wide.
# pylint: disable=protected-access


class TestChromeExtensionPlugin(chrome_extension.ChromeExtensionPlugin):
  """Chrome extension analysis plugin used for testing."""

  NAME = 'chrome_extension_test'

  _TEST_DATA_PATH = os.path.join(
      os.getcwd(), u'test_data', u'chrome_extensions')

  def _GetChromeWebStorePage(self, extension_id):
    """Retrieves the page for the extension from the Chrome store test data.

    Args:
      extension_id: string containing the extension identifier.

    Returns:
      A binary string containing the page content or None.
    """
    chrome_web_store_file = os.path.join(self._TEST_DATA_PATH, extension_id)
    if not os.path.exists(chrome_web_store_file):
      return

    file_object = open(chrome_web_store_file, 'rb')
    return file_object.read()


class ChromeExtensionTest(test_lib.AnalysisPluginTestCase):
  """Tests for the chrome extension analysis plugin."""

  # Few config options here.
  _MACOSX_PATHS = [
      u'/Users/dude/Libary/Application Data/Google/Chrome/Default/Extensions',
      (u'/Users/dude/Libary/Application Data/Google/Chrome/Default/Extensions/'
       u'apdfllckaahabafndbhieahigkjlhalf'),
      u'/private/var/log/system.log',
      u'/Users/frank/Library/Application Data/Google/Chrome/Default',
      u'/Users/hans/Library/Application Data/Google/Chrome/Default',
      (u'/Users/frank/Library/Application Data/Google/Chrome/Default/'
       u'Extensions/pjkljhegncpnkpknbcohdijeoejaedia'),
      u'/Users/frank/Library/Application Data/Google/Chrome/Default/Extensions']

  _WINDOWS_PATHS = [
      u'C:\\Users\\Dude\\SomeFolder\\Chrome\\Default\\Extensions',
      (u'C:\\Users\\Dude\\SomeNoneStandardFolder\\Chrome\\Default\\Extensions\\'
       u'hmjkmjkepdijhoojdojkdfohbdgmmhki'),
      (u'C:\\Users\\frank\\AppData\\Local\\Google\\Chrome\\Extensions\\'
       u'blpcfgokakmgnkcojhhkbfbldkacnbeo'),
      u'C:\\Users\\frank\\AppData\\Local\\Google\\Chrome\\Extensions',
      (u'C:\\Users\\frank\\AppData\\Local\\Google\\Chrome\\Extensions\\'
       u'icppfcnhkcmnfdhfhphakoifcfokfdhg'),
      u'C:\\Windows\\System32',
      u'C:\\Stuff/with path separator\\Folder']

  _MACOSX_USERS = [
      {u'name': u'root', u'path': u'/var/root', u'sid': u'0'},
      {u'name': u'frank', u'path': u'/Users/frank', u'sid': u'4052'},
      {u'name': u'hans', u'path': u'/Users/hans', u'sid': u'4352'},
      {u'name': u'dude', u'path': u'/Users/dude', u'sid': u'1123'}]

  _WINDOWS_USERS = [
      {u'name': u'dude', u'path': u'C:\\Users\\dude', u'sid': u'S-1'},
      {u'name': u'frank', u'path': u'C:\\Users\\frank', u'sid': u'S-2'}]

  def _CreateTestEventObject(self, path):
    """Create a test event object with a particular path."""
    event_object = events.EventObject()
    event_object.data_type = 'fs:stat'
    event_object.timestamp = 12345
    event_object.timestamp_desc = u'Some stuff'
    event_object.filename = path

    return event_object

  def testGetPathSegmentSeparator(self):
    """Tests the _GetPathSegmentSeparator function."""
    event_queue = single_process.SingleProcessQueue()
    analysis_plugin = TestChromeExtensionPlugin(event_queue)

    for path in self._MACOSX_PATHS:
      path_segment_separator = analysis_plugin._GetPathSegmentSeparator(path)
      self.assertEqual(path_segment_separator, u'/')

    for path in self._WINDOWS_PATHS:
      path_segment_separator = analysis_plugin._GetPathSegmentSeparator(path)
      self.assertEqual(path_segment_separator, u'\\')

  def testMacAnalyzerPlugin(self):
    """Test the plugin against mock events."""
    knowledge_base = self._SetUpKnowledgeBase(
        knowledge_base_values={u'users': self._MACOSX_USERS})

    event_queue = single_process.SingleProcessQueue()

    # Fill the incoming queue with events.
    test_queue_producer = plaso_queue.ItemQueueProducer(event_queue)
    test_queue_producer.ProduceItems([
        self._CreateTestEventObject(path) for path in self._MACOSX_PATHS])

    # Initialize plugin.
    analysis_plugin = TestChromeExtensionPlugin(event_queue)

    # Run the analysis plugin.
    analysis_report_queue_consumer = self._RunAnalysisPlugin(
        analysis_plugin, knowledge_base)
    analysis_reports = self._GetAnalysisReportsFromQueue(
        analysis_report_queue_consumer)

    self.assertEqual(len(analysis_reports), 1)

    analysis_report = analysis_reports[0]

    self.assertEqual(analysis_plugin._sep, u'/')

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

    self.assertEqual(analysis_report.text, expected_text)
    self.assertEqual(analysis_report.plugin_name, 'chrome_extension_test')

    expected_keys = set([u'frank', u'dude'])
    self.assertEqual(set(analysis_report.report_dict.keys()), expected_keys)

  def testWinAnalyzePlugin(self):
    """Test the plugin against mock events."""
    knowledge_base = self._SetUpKnowledgeBase(
        knowledge_base_values={u'users': self._WINDOWS_USERS})

    event_queue = single_process.SingleProcessQueue()

    # Fill the incoming queue with events.
    test_queue_producer = plaso_queue.ItemQueueProducer(event_queue)
    test_queue_producer.ProduceItems([
        self._CreateTestEventObject(path) for path in self._WINDOWS_PATHS])

    # Initialize plugin.
    analysis_plugin = TestChromeExtensionPlugin(event_queue)

    # Run the analysis plugin.
    analysis_report_queue_consumer = self._RunAnalysisPlugin(
        analysis_plugin, knowledge_base)
    analysis_reports = self._GetAnalysisReportsFromQueue(
        analysis_report_queue_consumer)

    self.assertEqual(len(analysis_reports), 1)

    analysis_report = analysis_reports[0]

    self.assertEqual(analysis_plugin._sep, u'\\')

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

    self.assertEqual(analysis_report.text, expected_text)
    self.assertEqual(analysis_report.plugin_name, 'chrome_extension_test')

    expected_keys = set([u'frank', u'dude'])
    self.assertEqual(set(analysis_report.report_dict.keys()), expected_keys)


if __name__ == '__main__':
  unittest.main()
