#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""Tests for the bloom analysis plugin."""

import collections
import unittest

from dfvfs.path import fake_path_spec

try:
  import flor
  from plaso.analysis import bloom
except ModuleNotFoundError:
  flor = None

from plaso.containers import events
from plaso.containers import reports
from plaso.lib import definitions

from tests.analysis import test_lib


@unittest.skipIf(flor is None, 'missing flor support')
class BloomTest(test_lib.AnalysisPluginTestCase):
  """Tests for the bloom database analysis plugin."""

  _EVENT_1_HASH = (
      '1e5f96de17b84a94f69e52a24b2942c4eca11bc9')

  _EVENT_2_HASH = (
      'aaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaa')

  _TEST_EVENTS = [
      {'data_type': 'fs:stat',
       'parser': 'filestat',
       'path_spec': fake_path_spec.FakePathSpec(
           location='C:\\WINDOWS\\system32\\know.exe'),
       'sha256_hash': _EVENT_1_HASH,
       'timestamp': '2015-01-01 17:00:00',
       'timestamp_desc': definitions.TIME_DESCRIPTION_CREATION},
      {'data_type': 'fs:stat:ntfs',
       'parser': 'filestat',
       'path_spec': fake_path_spec.FakePathSpec(
           location='C:\\WINDOWS\\system32\\unknown.exe'),
       'sha256_hash': _EVENT_2_HASH,
       'timestamp': '2016-01-01 17:00:00',
       'timestamp_desc': definitions.TIME_DESCRIPTION_CREATION}]

  def testExamineEventAndCompileReport(self):
    """Tests the ExamineEvent and CompileReport functions."""
    plugin = bloom.BloomAnalysisPlugin()
    # this file contains only one hash : _EVENT_1_HASH
    plugin.SetBloomDatabasePath('test_data/plaso.bloom')
    plugin.SetLabel('bloom_present')

    storage_writer = self._AnalyzeEvents(self._TEST_EVENTS, plugin)

    number_of_reports = storage_writer.GetNumberOfAttributeContainers(
        'analysis_report')
    self.assertEqual(number_of_reports, 1)

    analysis_report = storage_writer.GetAttributeContainerByIndex(
        reports.AnalysisReport.CONTAINER_TYPE, 0)
    self.assertIsNotNone(analysis_report)

    self.assertEqual(analysis_report.plugin_name, 'bloom')

    expected_analysis_counter = collections.Counter({
        'bloom_present': 1})
    self.assertEqual(
        analysis_report.analysis_counter, expected_analysis_counter)

    number_of_event_tags = storage_writer.GetNumberOfAttributeContainers(
        'event_tag')
    self.assertEqual(number_of_event_tags, 1)

    labels = []
    for event_tag in storage_writer.GetAttributeContainers(
        events.EventTag.CONTAINER_TYPE):
      labels.extend(event_tag.labels)
    self.assertEqual(len(labels), 1)

    expected_labels = ['bloom_present']
    self.assertEqual(labels, expected_labels)


if __name__ == '__main__':
  unittest.main()
