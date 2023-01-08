#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""Tests for the hash tagging analysis plugin."""

import collections
import unittest

from dfvfs.path import fake_path_spec

from plaso.analysis import hash_tagging
from plaso.containers import events
from plaso.containers import reports
from plaso.lib import definitions

from tests.analysis import test_lib


class TestHashTaggingAnalysisPlugin(hash_tagging.HashTaggingAnalysisPlugin):
  """Hash tagging analysis plugin for testing."""

  DATA_TYPES = frozenset(['fs:stat', 'fs:stat:ntfs'])

  SUPPORTED_HASHES = frozenset(['md5', 'sha256'])

  NAME = 'hash_tagging_test'

  _TEST_HASH_SET = frozenset([
      '2d79fcc6b02a2e183a0cb30e0e25d103f42badda9fbf86bbee06f93aa3855aff'])

  def _Analyze(self, hashes):
    """Analyzes a list of hashes.

    Args:
      hashes (list[str]): list of hashes to look up.

    Returns:
      list[HashAnalysis]: list of results of analyzing the hashes.
    """
    hash_analyses = []
    for digest in hashes:
      response = bool(digest in self._TEST_HASH_SET)
      hash_analysis = hash_tagging.HashAnalysis(digest, response)
      hash_analyses.append(hash_analysis)

    return hash_analyses

  def _GenerateLabels(self, hash_information):
    """Generates a labels that will be used in the event tag.

    Args:
      hash_information (bool): True if the analyzer received a response from
          the test hash analyzer indicating that the hash was present in the
          test hash set.

    Returns:
      list[str]: labels to use in the event tag.
    """
    if hash_information:
      return ['hashtag']
    return []


class HashTaggingAnalysisPluginTest(test_lib.AnalysisPluginTestCase):
  """Tests for the hash tagging analysis plugin."""

  _EVENT_1_HASH = (
      '2d79fcc6b02a2e183a0cb30e0e25d103f42badda9fbf86bbee06f93aa3855aff')

  _EVENT_2_HASH = (
      'aaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaa')

  _TEST_EVENTS = [
      {'_parser_chain': 'filestat',
       'data_type': 'fs:stat',
       'path_spec': fake_path_spec.FakePathSpec(
           location='C:\\WINDOWS\\system32\\good.exe'),
       'sha256_hash': _EVENT_1_HASH,
       'timestamp': '2015-01-01 17:00:00',
       'timestamp_desc': definitions.TIME_DESCRIPTION_CREATION},
      {'_parser_chain': 'filestat',
       'data_type': 'fs:stat:ntfs',
       'path_spec': fake_path_spec.FakePathSpec(
           location='C:\\WINDOWS\\system32\\evil.exe'),
       'sha256_hash': _EVENT_2_HASH,
       'timestamp': '2016-01-01 17:00:00',
       'timestamp_desc': definitions.TIME_DESCRIPTION_CREATION}]

  def testExamineEventAndCompileReport(self):
    """Tests the ExamineEvent and CompileReport functions."""
    plugin = TestHashTaggingAnalysisPlugin()

    storage_writer = self._AnalyzeEvents(self._TEST_EVENTS, plugin)

    number_of_reports = storage_writer.GetNumberOfAttributeContainers(
        'analysis_report')
    self.assertEqual(number_of_reports, 1)

    analysis_report = storage_writer.GetAttributeContainerByIndex(
        reports.AnalysisReport.CONTAINER_TYPE, 0)
    self.assertIsNotNone(analysis_report)

    self.assertEqual(analysis_report.plugin_name, 'hash_tagging_test')

    expected_analysis_counter = collections.Counter({
        'hashtag': 1})
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

    expected_labels = ['hashtag']
    self.assertEqual(labels, expected_labels)

    # Tests a hash that is not set.
    plugin = TestHashTaggingAnalysisPlugin()
    plugin.SetLookupHash('md5')

    storage_writer = self._AnalyzeEvents(self._TEST_EVENTS, plugin)

    number_of_reports = storage_writer.GetNumberOfAttributeContainers(
        'analysis_report')
    self.assertEqual(number_of_reports, 1)

    analysis_report = storage_writer.GetAttributeContainerByIndex(
        reports.AnalysisReport.CONTAINER_TYPE, 0)
    self.assertIsNotNone(analysis_report)

    self.assertEqual(analysis_report.plugin_name, 'hash_tagging_test')

    expected_analysis_counter = collections.Counter({})
    self.assertEqual(
        analysis_report.analysis_counter, expected_analysis_counter)

    number_of_event_tags = storage_writer.GetNumberOfAttributeContainers(
        'event_tag')
    self.assertEqual(number_of_event_tags, 0)

    labels = []
    for event_tag in storage_writer.GetAttributeContainers(
        events.EventTag.CONTAINER_TYPE):
      labels.extend(event_tag.labels)
    self.assertEqual(len(labels), 0)

  def testSetLookupHash(self):
    """Tests the SetLookupHash function."""
    plugin = TestHashTaggingAnalysisPlugin()

    plugin.SetLookupHash('md5')

    with self.assertRaises(ValueError):
      plugin.SetLookupHash('bogus')


if __name__ == '__main__':
  unittest.main()
