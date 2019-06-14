#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""Tests for the chrome extension analysis plugin."""

from __future__ import unicode_literals

import os
import unittest

from plaso.analysis import chrome_extension
from plaso.lib import definitions
from plaso.lib import timelib

from tests import test_lib as shared_test_lib
from tests.analysis import test_lib


class MockChromeExtensionPlugin(chrome_extension.ChromeExtensionPlugin):
  """Chrome extension analysis plugin used for testing."""

  NAME = 'chrome_extension_test'

  _TEST_DATA_PATH = os.path.join(os.getcwd(), 'test_data')

  def _GetChromeWebStorePage(self, extension_identifier):
    """Retrieves the page for the extension from the Chrome store website.

    Args:
      extension_identifier (str): Chrome extension identifier.

    Returns:
      str: page content or None if not available.
    """
    chrome_web_store_file = shared_test_lib.GetTestFilePath([
        'chrome_extensions', extension_identifier])
    if not os.path.exists(chrome_web_store_file):
      return None

    with open(chrome_web_store_file, 'rb') as file_object:
      page_content = file_object.read()

    return page_content.decode('utf-8')

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

  _MACOS_PATHS = [
      '/Users/dude/Libary/Application Data/Google/Chrome/Default/Extensions',
      ('/Users/dude/Libary/Application Data/Google/Chrome/Default/Extensions/'
       'apdfllckaahabafndbhieahigkjlhalf'),
      '/private/var/log/system.log',
      '/Users/frank/Library/Application Data/Google/Chrome/Default',
      '/Users/hans/Library/Application Data/Google/Chrome/Default',
      ('/Users/frank/Library/Application Data/Google/Chrome/Default/'
       'Extensions/pjkljhegncpnkpknbcohdijeoejaedia'),
      '/Users/frank/Library/Application Data/Google/Chrome/Default/Extensions']

  _MACOS_TEST_EVENTS = [
      {'data_type': 'fs:stat',
       'filename': path,
       'timestamp': timelib.Timestamp.CopyFromString('2015-01-01 17:00:00'),
       'timestamp_desc': definitions.TIME_DESCRIPTION_UNKNOWN}
      for path in _MACOS_PATHS]

  _MACOS_USERS = [
      {'name': 'root', 'path': '/var/root', 'sid': '0'},
      {'name': 'frank', 'path': '/Users/frank', 'sid': '4052'},
      {'name': 'hans', 'path': '/Users/hans', 'sid': '4352'},
      {'name': 'dude', 'path': '/Users/dude', 'sid': '1123'}]

  _WINDOWS_PATHS = [
      'C:\\Users\\Dude\\SomeFolder\\Chrome\\Default\\Extensions',
      ('C:\\Users\\Dude\\SomeNoneStandardFolder\\Chrome\\Default\\Extensions\\'
       'hmjkmjkepdijhoojdojkdfohbdgmmhki'),
      ('C:\\Users\\frank\\AppData\\Local\\Google\\Chrome\\Extensions\\'
       'blpcfgokakmgnkcojhhkbfbldkacnbeo'),
      'C:\\Users\\frank\\AppData\\Local\\Google\\Chrome\\Extensions',
      ('C:\\Users\\frank\\AppData\\Local\\Google\\Chrome\\Extensions\\'
       'icppfcnhkcmnfdhfhphakoifcfokfdhg'),
      'C:\\Windows\\System32',
      'C:\\Stuff/with path separator\\Folder']

  _WINDOWS_TEST_EVENTS = [
      {'data_type': 'fs:stat',
       'filename': path,
       'timestamp': timelib.Timestamp.CopyFromString('2015-01-01 17:00:00'),
       'timestamp_desc': definitions.TIME_DESCRIPTION_UNKNOWN}
      for path in _WINDOWS_PATHS]

  _WINDOWS_USERS = [
      {'name': 'dude', 'path': 'C:\\Users\\dude', 'sid': 'S-1'},
      {'name': 'frank', 'path': 'C:\\Users\\frank', 'sid': 'S-2'}]

  def testGetPathSegmentSeparator(self):
    """Tests the _GetPathSegmentSeparator function."""
    test_file_path = self._GetTestFilePath(['chrome_extensions'])
    self._SkipIfPathNotExists(test_file_path)

    plugin = MockChromeExtensionPlugin()

    for path in self._MACOS_PATHS:
      path_segment_separator = plugin._GetPathSegmentSeparator(path)
      self.assertEqual(path_segment_separator, '/')

    for path in self._WINDOWS_PATHS:
      path_segment_separator = plugin._GetPathSegmentSeparator(path)
      self.assertEqual(path_segment_separator, '\\')

  def testExamineEventAndCompileReportMacOSPaths(self):
    """Tests the ExamineEvent and CompileReport functions on MacOS paths."""
    test_file_path = self._GetTestFilePath(['chrome_extensions'])
    self._SkipIfPathNotExists(test_file_path)

    plugin = MockChromeExtensionPlugin()
    storage_writer = self._AnalyzeEvents(
        self._MACOS_TEST_EVENTS, plugin, knowledge_base_values={
            'users': self._MACOS_USERS})

    self.assertEqual(len(storage_writer.analysis_reports), 1)

    analysis_report = storage_writer.analysis_reports[0]

    # Due to the behavior of the join one additional empty string at the end
    # is needed to create the last empty line.
    expected_text = '\n'.join([
        ' == USER: dude ==',
        '  Google Drive [apdfllckaahabafndbhieahigkjlhalf]',
        '',
        ' == USER: frank ==',
        '  Gmail [pjkljhegncpnkpknbcohdijeoejaedia]',
        '',
        ''])

    self.assertEqual(analysis_report.text, expected_text)
    self.assertEqual(analysis_report.plugin_name, 'chrome_extension_test')

    expected_keys = set(['frank', 'dude'])
    self.assertEqual(set(analysis_report.report_dict.keys()), expected_keys)

  def testExamineEventAndCompileReportWindowsPaths(self):
    """Tests the ExamineEvent and CompileReport functions on Windows paths."""
    test_file_path = self._GetTestFilePath(['chrome_extensions'])
    self._SkipIfPathNotExists(test_file_path)

    plugin = MockChromeExtensionPlugin()
    storage_writer = self._AnalyzeEvents(
        self._WINDOWS_TEST_EVENTS, plugin, knowledge_base_values={
            'users': self._WINDOWS_USERS})

    self.assertEqual(len(storage_writer.analysis_reports), 1)

    analysis_report = storage_writer.analysis_reports[0]

    # Due to the behavior of the join one additional empty string at the end
    # is needed to create the last empty line.
    expected_text = '\n'.join([
        ' == USER: dude ==',
        '  Google Keep - notes and lists [hmjkmjkepdijhoojdojkdfohbdgmmhki]',
        '',
        ' == USER: frank ==',
        '  Google Play Music [icppfcnhkcmnfdhfhphakoifcfokfdhg]',
        '  YouTube [blpcfgokakmgnkcojhhkbfbldkacnbeo]',
        '',
        ''])

    self.assertEqual(analysis_report.text, expected_text)
    self.assertEqual(analysis_report.plugin_name, 'chrome_extension_test')

    expected_keys = set(['frank', 'dude'])
    self.assertEqual(set(analysis_report.report_dict.keys()), expected_keys)


if __name__ == '__main__':
  unittest.main()
