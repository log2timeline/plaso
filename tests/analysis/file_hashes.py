#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""Tests for the unique hashes analysis plugin."""

from __future__ import unicode_literals

import unittest

from dfvfs.path import fake_path_spec

from plaso.analysis import file_hashes
from plaso.lib import definitions
from plaso.lib import timelib

from tests.analysis import test_lib


class UniqueHashesTest(test_lib.AnalysisPluginTestCase):
  """Test for the unique hashes analysis plugin."""

  _TEST_EVENTS = [
      {'data_type': 'test:event',
       'pathspec': fake_path_spec.FakePathSpec(
           location='/var/testing directory with space/file.txt'),
       'test_hash': '4',
       'timestamp': timelib.Timestamp.CopyFromString('2015-01-01 17:00:00'),
       'timestamp_desc': definitions.TIME_DESCRIPTION_UNKNOWN},
      {'data_type': 'test:event',
       'pathspec': fake_path_spec.FakePathSpec(
           location='C:\\Windows\\a.file.txt'),
       'test_hash': '4',
       'timestamp': timelib.Timestamp.CopyFromString('2015-01-01 17:00:01'),
       'timestamp_desc': definitions.TIME_DESCRIPTION_UNKNOWN},
      {'data_type': 'test:event',
       'pathspec': fake_path_spec.FakePathSpec(location='/opt/dfvfs'),
       'test_hash': '4',
       'timestamp': timelib.Timestamp.CopyFromString('2015-01-01 17:00:02'),
       'timestamp_desc': definitions.TIME_DESCRIPTION_UNKNOWN},
      {'alternate_test_hash': '5',
       'data_type': 'test:event',
       'pathspec': fake_path_spec.FakePathSpec(location='/opt/2hash_file'),
       'test_hash': '4',
       'timestamp': timelib.Timestamp.CopyFromString('2015-01-01 17:00:03'),
       'timestamp_desc': definitions.TIME_DESCRIPTION_UNKNOWN},
      {'data_type': 'test:event',
       'pathspec': fake_path_spec.FakePathSpec(location='/opt/no_hash_file'),
       'timestamp': timelib.Timestamp.CopyFromString('2015-01-01 17:00:04'),
       'timestamp_desc': definitions.TIME_DESCRIPTION_UNKNOWN}]

  def testExamineEventAndCompileReport(self):
    """Tests the ExamineEvent and CompileReport functions."""
    plugin = file_hashes.FileHashesPlugin()
    storage_writer = self._AnalyzeEvents(self._TEST_EVENTS, plugin)

    self.assertEqual(len(storage_writer.analysis_reports), 1)

    analysis_report = storage_writer.analysis_reports[0]

    expected_text = (
        'Listing file paths and hashes\n'
        'FAKE:/opt/2hash_file: alternate_test_hash=5 test_hash=4\n'
        'FAKE:/opt/dfvfs: test_hash=4\n'
        'FAKE:/opt/no_hash_file:\n'
        'FAKE:/var/testing directory with space/file.txt: test_hash=4\n'
        'FAKE:C:\\Windows\\a.file.txt: test_hash=4\n')

    self.assertEqual(expected_text, analysis_report.text)
    self.assertEqual(analysis_report.plugin_name, 'file_hashes')


if __name__ == '__main__':
  unittest.main()
