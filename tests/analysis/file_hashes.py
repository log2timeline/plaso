#!/usr/bin/python
# -*- coding: utf-8 -*-
"""Tests for the unique hashes analysis plugin."""

import unittest

from dfvfs.path import fake_path_spec

from plaso.analysis import file_hashes
from plaso.analysis import mediator

from tests.analysis import test_lib


class UniqueHashesTest(test_lib.AnalysisPluginTestCase):
  """Test for the unique hashes analysis plugin."""

  _TEST_EVENTS = [
      {u'pathspec': fake_path_spec.FakePathSpec(
          location=u'/var/testing directory with space/file.txt'),
       u'test_hash': u'4'},
      {u'pathspec': fake_path_spec.FakePathSpec(
          location=u'C:\\Windows\\a.file.txt'),
       u'test_hash': u'4'},
      {u'pathspec': fake_path_spec.FakePathSpec(
          location=u'/opt/dfvfs'),
       u'test_hash': u'4'},
      {u'pathspec': fake_path_spec.FakePathSpec(
          location=u'/opt/2hash_file'),
       u'test_hash': u'4',
       u'alternate_test_hash': u'5'},
      {u'pathspec': fake_path_spec.FakePathSpec(
          location=u'/opt/no_hash_file')}
  ]

  def testExamineEventAndCompileReport(self):
    """Tests the ExamineEvent and CompileReport functions."""
    knowledge_base = self._SetUpKnowledgeBase()
    analysis_mediator = mediator.AnalysisMediator(None, knowledge_base)

    plugin = file_hashes.FileHashesPlugin()

    for event_dictionary in self._TEST_EVENTS:
      event = self._CreateTestEventObject(event_dictionary)
      plugin.ExamineEvent(analysis_mediator, event)

    analysis_report = plugin.CompileReport(analysis_mediator)
    self.assertIsNotNone(analysis_report)

    expected_text = (
        u'Listing file paths and hashes\n'
        u'FAKE:/opt/2hash_file: alternate_test_hash=5 test_hash=4\n'
        u'FAKE:/opt/dfvfs: test_hash=4\n'
        u'FAKE:/opt/no_hash_file:\n'
        u'FAKE:/var/testing directory with space/file.txt: test_hash=4\n'
        u'FAKE:C:\\Windows\\a.file.txt: test_hash=4\n')

    self.assertEqual(expected_text, analysis_report.text)
    self.assertEqual(analysis_report.plugin_name, u'file_hashes')


if __name__ == '__main__':
  unittest.main()
