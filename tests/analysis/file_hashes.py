#!/usr/bin/python
# -*- coding: utf-8 -*-
"""Tests for the unique hashes analysis plugin."""

import unittest

from dfvfs.path import fake_path_spec

from plaso.analysis import file_hashes
from plaso.containers import events
from plaso.engine import queue
from plaso.engine import single_process

from tests.analysis import test_lib


class UniqueHashesTest(test_lib.AnalysisPluginTestCase):
  """Test for the unique hashes analysis plugin."""
  _EVENT_DICTS = [
      {u'path_spec': fake_path_spec.FakePathSpec(
          u'/var/testing directory with space/file.txt'),
       u'test_hash': u'4'},
      {u'path_spec': fake_path_spec.FakePathSpec(u'C:\\Windows\\a.file.txt'),
       u'test_hash': u'4'},
      {u'path_spec': fake_path_spec.FakePathSpec(u'/opt/dfvfs'),
       u'test_hash': u'4'},
      {u'path_spec': fake_path_spec.FakePathSpec(u'/opt/2hash_file'),
       u'test_hash': u'4',
       u'alternate_test_hash': u'5'},
      {u'path_spec': fake_path_spec.FakePathSpec(u'/opt/no_hash_file')}
  ]

  def _CreateTestEventObject(self, event_dict):
    """Create a test event object.

    Args:
      service_event: A hash containing attributes of an event to add to the
                     queue.

    Returns:
      An EventObject to test with.
    """
    event_object = events.EventObject()
    event_object.pathspec = event_dict[u'path_spec']
    for attrib in event_dict.keys():
      if attrib.endswith(u'_hash'):
        setattr(event_object, attrib, event_dict[attrib])
    return event_object

  def testEvents(self):
    """Test the plugin against mock events."""
    event_queue = single_process.SingleProcessQueue()

    # Fill the incoming queue with events.
    test_queue_producer = queue.ItemQueueProducer(event_queue)
    event_objects = [
        self._CreateTestEventObject(event_dict)
        for event_dict in self._EVENT_DICTS]
    test_queue_producer.ProduceItems(event_objects)

    # Initialize plugin.
    analysis_plugin = file_hashes.FileHashesPlugin(event_queue)

    # Run the analysis plugin.
    knowledge_base = self._SetUpKnowledgeBase()
    analysis_report_queue_consumer = self._RunAnalysisPlugin(
        analysis_plugin, knowledge_base)
    analysis_reports = self._GetAnalysisReportsFromQueue(
        analysis_report_queue_consumer)

    self.assertEqual(len(analysis_reports), 1)

    analysis_report = analysis_reports[0]

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
