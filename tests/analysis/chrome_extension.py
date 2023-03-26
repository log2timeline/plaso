#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""Tests for the Chrome extension analysis plugin."""

import collections
import os
import unittest

from plaso.analysis import chrome_extension
from plaso.containers import artifacts
from plaso.containers import reports
from plaso.lib import definitions

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
      str: page content or None if not available.
    """
    chrome_web_store_file = shared_test_lib.GetTestFilePath([
        'chrome_extensions', extension_identifier])
    if not os.path.exists(chrome_web_store_file):
      return None

    with open(chrome_web_store_file, 'rb') as file_object:
      page_content = file_object.read()

    return page_content.decode('utf-8')


class ChromeExtensionTest(test_lib.AnalysisPluginTestCase):
  """Tests for the Chrome extension analysis plugin."""

  # pylint: disable=protected-access

  _MACOS_PATHS = [
      '/Users/dude/Library/Application Data/Google/Chrome/Default/Extensions',
      ('/Users/dude/Library/Application Data/Google/Chrome/Default/Extensions/'
       'apdfllckaahabafndbhieahigkjlhalf'),
      '/private/var/log/system.log',
      '/Users/frank/Library/Application Data/Google/Chrome/Default',
      '/Users/hans/Library/Application Data/Google/Chrome/Default',
      ('/Users/frank/Library/Application Data/Google/Chrome/Default/'
       'Extensions/pjkljhegncpnkpknbcohdijeoejaedia'),
      '/Users/frank/Library/Application Data/Google/Chrome/Default/Extensions']

  _MACOS_TEST_EVENTS = [
      {'_parser_chain': 'filestat',
       'data_type': 'fs:stat',
       'filename': path,
       'timestamp': '2015-01-01 17:00:00',
       'timestamp_desc': definitions.TIME_DESCRIPTION_UNKNOWN}
      for path in _MACOS_PATHS]

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
      {'_parser_chain': 'filestat',
       'data_type': 'fs:stat',
       'filename': path,
       'timestamp': '2015-01-01 17:00:00',
       'timestamp_desc': definitions.TIME_DESCRIPTION_UNKNOWN}
      for path in _WINDOWS_PATHS]

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

    user_accounts = [
        artifacts.UserAccountArtifact(
            identifier='0', user_directory='/var/root', username='root'),
        artifacts.UserAccountArtifact(
            identifier='1123', user_directory='/Users/dude', username='dude'),
        artifacts.UserAccountArtifact(
            identifier='4052', user_directory='/Users/frank', username='frank'),
        artifacts.UserAccountArtifact(
            identifier='4352', user_directory='/Users/hans', username='hans')]

    plugin = MockChromeExtensionPlugin()
    storage_writer = self._AnalyzeEvents(
        self._MACOS_TEST_EVENTS, plugin, user_accounts=user_accounts)

    analysis_results = list(storage_writer.GetAttributeContainers(
        'chrome_extension_analysis_result'))
    self.assertEqual(len(analysis_results), 2)

    analysis_result = analysis_results[0]
    self.assertEqual(analysis_result.extension, 'Google Drive')
    self.assertEqual(
        analysis_result.extension_identifier,
        'apdfllckaahabafndbhieahigkjlhalf')
    self.assertEqual(analysis_result.username, 'dude')

    number_of_reports = storage_writer.GetNumberOfAttributeContainers(
        'analysis_report')
    self.assertEqual(number_of_reports, 1)

    analysis_report = storage_writer.GetAttributeContainerByIndex(
        reports.AnalysisReport.CONTAINER_TYPE, 0)
    self.assertIsNotNone(analysis_report)

    self.assertEqual(analysis_report.plugin_name, 'chrome_extension_test')

    expected_analysis_counter = collections.Counter({
        'dude': 1,
        'frank': 1})
    self.assertEqual(
        analysis_report.analysis_counter, expected_analysis_counter)

  def testExamineEventAndCompileReportWindowsPaths(self):
    """Tests the ExamineEvent and CompileReport functions on Windows paths."""
    test_file_path = self._GetTestFilePath(['chrome_extensions'])
    self._SkipIfPathNotExists(test_file_path)

    user_accounts = [
        artifacts.UserAccountArtifact(
            identifier='S-1', path_separator='\\',
            user_directory='C:\\Users\\dude', username='dude'),
        artifacts.UserAccountArtifact(
            identifier='S-2', path_separator='\\',
            user_directory='C:\\Users\\frank', username='frank')]

    plugin = MockChromeExtensionPlugin()
    storage_writer = self._AnalyzeEvents(
        self._WINDOWS_TEST_EVENTS, plugin, user_accounts=user_accounts)

    analysis_results = list(storage_writer.GetAttributeContainers(
        'chrome_extension_analysis_result'))
    self.assertEqual(len(analysis_results), 3)

    analysis_result = analysis_results[0]
    self.assertEqual(analysis_result.extension, 'Google Keep - notes and lists')
    self.assertEqual(
        analysis_result.extension_identifier,
        'hmjkmjkepdijhoojdojkdfohbdgmmhki')
    self.assertEqual(analysis_result.username, 'dude')

    number_of_reports = storage_writer.GetNumberOfAttributeContainers(
        'analysis_report')
    self.assertEqual(number_of_reports, 1)

    analysis_report = storage_writer.GetAttributeContainerByIndex(
        reports.AnalysisReport.CONTAINER_TYPE, 0)
    self.assertIsNotNone(analysis_report)

    self.assertEqual(analysis_report.plugin_name, 'chrome_extension_test')

    expected_analysis_counter = collections.Counter({
        'dude': 1,
        'frank': 2})
    self.assertEqual(
        analysis_report.analysis_counter, expected_analysis_counter)


if __name__ == '__main__':
  unittest.main()
