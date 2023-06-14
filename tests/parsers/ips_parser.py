# -*- coding: utf-8 -*-
"""Tests for the ips log file parser."""

import unittest

from dfvfs.helpers import text_file

from plaso.parsers import ips_parser
# Register all plugins.
from plaso.parsers import ips_plugins  # pylint: disable=unused-import

from tests.parsers import test_lib


class IPSFileTest(test_lib.ParserTestCase):
  """Tests for the IPS log file."""

  def testOpen(self):
    """Tests the Open function."""
    path_segments = ['ips_files', 'recoverylogd-2023-06-08-144913.ips']

    ips_log_path = self._GetTestFilePath(path_segments)
    self._SkipIfPathNotExists(ips_log_path)

    file_entry = self._GetTestFileEntry(path_segments)
    file_object = file_entry.GetFileObject()
    text_file_object = text_file.TextFile(file_object)

    ips_log_file = ips_parser.IPSFile()
    ips_log_file.Open(text_file_object)

    expected_header_keys = [
        'app_name', 'timestamp', 'app_version', 'slice_uuid', 'build_version',
        'platform', 'share_with_app_devs', 'is_first_party', 'bug_type',
        'os_version', 'roots_installed', 'incident_id', 'name']

    self.assertEqual(list(ips_log_file.header.keys()), expected_header_keys)

    expected_content_keys = [
        'uptime', 'procRole', 'version', 'userID', 'deployVersion',
        'modelCode', 'coalitionID', 'osVersion', 'captureTime', 'incident',
        'pid', 'cpuType', 'roots_installed', 'bug_type', 'procLaunch',
        'procStartAbsTime', 'procExitAbsTime', 'procName', 'procPath',
        'parentProc', 'parentPid', 'coalitionName', 'crashReporterKey',
        'throttleTimeout', 'codeSigningID', 'codeSigningTeamID',
        'codeSigningFlags', 'codeSigningValidationCategory',
        'codeSigningTrustLevel', 'exception', 'termination', 'asi',
        'faultingThread', 'threads', 'usedImages', 'sharedCache', 'vmSummary',
        'legacyInfo', 'logWritingSignature']

    self.assertEqual(list(ips_log_file.content.keys()), expected_content_keys)


class IPSParserTest(test_lib.ParserTestCase):
  """IPS parser plugin test case."""
  def testParseFileEntry(self):
    """Tests the ParseFileEntry method."""
    parser = ips_parser.IPSParser()

    storage_writer = self._ParseFile(
      ['ips_files', 'recoverylogd-2023-06-08-144913.ips'], parser)

    number_of_event_data = storage_writer.GetNumberOfAttributeContainers(
        'event_data')
    self.assertEqual(number_of_event_data, 1)

    number_of_warnings = storage_writer.GetNumberOfAttributeContainers(
        'extraction_warning')
    self.assertEqual(number_of_warnings, 0)

    number_of_warnings = storage_writer.GetNumberOfAttributeContainers(
        'recovery_warning')
    self.assertEqual(number_of_warnings, 0)


if __name__ == '__main__':
  unittest.main()
