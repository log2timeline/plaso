#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""Tests for the ips log file parser."""

import unittest

from plaso.parsers import ips_parser
# Register all plugins.
from plaso.parsers import ips_plugins  # pylint: disable=unused-import

from tests.parsers import test_lib


class IPSFileTest(test_lib.ParserTestCase):
  """Tests for the IPS log file."""

  def testOpen(self):
    """Tests the Open function."""
    ips_log_path = self._GetTestFilePath(['ips', 'application_crash_log.ips'])
    self._SkipIfPathNotExists(ips_log_path)

    ips_log_file = ips_parser.IPSFile()

    with open(ips_log_path, 'r', encoding='utf-8') as file_object:
      ips_log_file.Open(file_object)

      expected_header_keys = [
          'app_name', 'timestamp', 'app_version', 'slice_uuid', 'adam_id',
          'build_version', 'platform', 'bundleID', 'share_with_app_devs',
          'is_first_party', 'bug_type', 'os_version', 'incident_id', 'name']

      self.assertEqual(list(ips_log_file.header.keys()), expected_header_keys)

      expected_content_keys = [
          'uptime', 'procLaunch', 'procRole', 'version', 'userID',
          'deployVersion', 'modelCode', 'procStartAbsTime', 'coalitionID',
          'osVersion', 'captureTime', 'incident', 'bug_type', 'pid',
          'procExitAbsTime', 'cpuType', 'procName', 'procPath', 'bundleInfo',
          'storeInfo', 'parentProc', 'parentPid', 'coalitionName',
          'crashReporterKey', 'isCorpse', 'exception', 'termination',
          'faultingThread', 'threads', 'usedImages', 'sharedCache', 'vmSummary',
          'legacyInfo', 'trialInfo']

      self.assertEqual(list(ips_log_file.content.keys()), expected_content_keys)


class IPSParserTest(test_lib.ParserTestCase):
  """Tests for the IPS file parser."""

  # pylint: disable=protected-access

  def testEnablePlugins(self):
    """Tests the EnablePlugins function."""
    parser = ips_parser.IPSParser()

    number_of_plugins = len(parser._plugin_classes)

    parser.EnablePlugins([])
    self.assertEqual(len(parser._plugins), 0)

    parser.EnablePlugins(parser.ALL_PLUGINS)
    self.assertEqual(len(parser._plugins), number_of_plugins)

    parser.EnablePlugins(['apple_crash_log'])
    self.assertEqual(len(parser._plugins), 1)


if __name__ == '__main__':
  unittest.main()
