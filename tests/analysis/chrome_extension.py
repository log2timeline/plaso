#!/usr/bin/python
# -*- coding: utf-8 -*-
"""Tests for the chrome extension analysis plugin."""

import os
import unittest

from plaso.analysis import chrome_extension

from tests import test_lib as shared_test_lib
from tests.analysis import test_lib


class MockChromeExtensionPlugin(chrome_extension.ChromeExtensionPlugin):
  """Chrome extension analysis plugin used for testing."""

  NAME = 'chrome_extension_test'

  def _GetChromeWebStorePage(self, extension_identifier):
    """Retrieves the page for the extension from the Chrome store website.

    Args:
      extension_identifier (str): Chrome extension identifier.

    Returns:
      str: page content or None.
    """
    chrome_web_store_file = shared_test_lib.GetTestFilePath([
        u'chrome_extensions', extension_identifier])
    if not os.path.exists(chrome_web_store_file):
      return

    with open(chrome_web_store_file, 'rb') as file_object:
      page_content = file_object.read()

    return page_content.decode(u'utf-8')

  def _GetTestFilePath(self, path_segments):
    """Retrieves the path of a test file in the test data directory.

    Args:
    path_segments (list[str]): path segments inside the test data directory.

    Returns:
      str: path of the test file.
    """
    # Note that we need to pass the individual path segments to os.path.join
    # and not a list.
    return os.path.join(self._TEST_DATA_PATH, *path_segments)


class ChromeExtensionTest(test_lib.AnalysisPluginTestCase):
  """Tests for the chrome extension analysis plugin."""

  # pylint: disable=protected-access

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

  @shared_test_lib.skipUnlessHasTestFile([u'chrome_extensions'])
  def testGetPathSegmentSeparator(self):
    """Tests the _GetPathSegmentSeparator function."""
    plugin = MockChromeExtensionPlugin()

    for path in self._MACOSX_PATHS:
      path_segment_separator = plugin._GetPathSegmentSeparator(path)
      self.assertEqual(path_segment_separator, u'/')

    for path in self._WINDOWS_PATHS:
      path_segment_separator = plugin._GetPathSegmentSeparator(path)
      self.assertEqual(path_segment_separator, u'\\')

  @shared_test_lib.skipUnlessHasTestFile([u'chrome_extensions'])
  def testExamineEventAndCompileReportMacOSXPaths(self):
    """Tests the ExamineEvent and CompileReport functions on Mac OS X paths."""
    events = []
    for path in self._MACOSX_PATHS:
      event_dictionary = {
          u'data_type': u'fs:stat',
          u'filename': path,
          u'timestamp': 12345,
          u'timestamp_desc': u'Some stuff'}

      event = self._CreateTestEventObject(event_dictionary)
      events.append(event)

    plugin = MockChromeExtensionPlugin()
    storage_writer = self._AnalyzeEvents(
        events, plugin, knowledge_base_values={u'users': self._MACOSX_USERS})

    self.assertEqual(len(storage_writer.analysis_reports), 1)

    analysis_report = storage_writer.analysis_reports[0]

    self.assertEqual(plugin._sep, u'/')

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

  @shared_test_lib.skipUnlessHasTestFile([u'chrome_extensions'])
  def testExamineEventAndCompileReportWindowsPaths(self):
    """Tests the ExamineEvent and CompileReport functions on Windows paths."""
    events = []
    for path in self._WINDOWS_PATHS:
      event_dictionary = {
          u'data_type': u'fs:stat',
          u'filename': path,
          u'timestamp': 12345,
          u'timestamp_desc': u'Some stuff'}

      event = self._CreateTestEventObject(event_dictionary)
      events.append(event)

    plugin = MockChromeExtensionPlugin()
    storage_writer = self._AnalyzeEvents(
        events, plugin, knowledge_base_values={u'users': self._WINDOWS_USERS})

    self.assertEqual(len(storage_writer.analysis_reports), 1)

    analysis_report = storage_writer.analysis_reports[0]

    self.assertEqual(plugin._sep, u'\\')

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
