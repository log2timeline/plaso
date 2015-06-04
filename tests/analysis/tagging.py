#!/usr/bin/python
# -*- coding: utf-8 -*-
"""Tests for the tagging analysis plugin."""

import unittest

from plaso.analysis import tagging
from plaso.engine import queue
from plaso.engine import single_process
from plaso.lib import event
from plaso.lib import timelib

from tests.analysis import test_lib


class TestPrefetchEvent(event.EventObject):
  """A test event type for the tagging analysis plugin."""
  DATA_TYPE = u'windows:prefetch'


class TestChromeDownloadEvent(event.EventObject):
  """A test event type for the tagging analysis plugin."""
  DATA_TYPE = u'chrome:history:file_downloaded'


class TaggingTest(test_lib.AnalysisPluginTestCase):
  """Test for the tagging analysis plugin."""
  TEST_TAG_FILE_NAME = u'test_tag_file.txt'
  TEST_EVENTS = [
      {u'event_type': u'prefetch',
       u'timestamp': timelib.Timestamp.CopyFromString(u'2015-05-01 15:12:00'),
       u'attributes': {}
      },
      {u'event_type': u'chrome_download',
       u'timestamp': timelib.Timestamp.CopyFromString(u'2015-05-01 05:06:00'),
       u'attributes': {}
      },
      {u'event_type': u'something_else',
       u'timestamp': timelib.Timestamp.CopyFromString(u'2015-02-19 08:00:01'),
       u'attributes': {}
      }
  ]

  def _CreateTestEventObject(self, test_event_dict):
    """Create a basic event object to test the plugin on."""
    if test_event_dict[u'event_type'] == u'prefetch':
      event_object = TestPrefetchEvent()
    elif test_event_dict[u'event_type'] == u'chrome_download':
      event_object = TestChromeDownloadEvent()
    else:
      event_object = event.EventObject()
    event_object.timestamp = test_event_dict[u'timestamp']
    for key, value in test_event_dict[u'attributes']:
      setattr(event_object, key, value)
    return event_object

  def testParseTagFile(self):
    """Test that the tagging plugin can parse a tag definition file."""
    event_queue = single_process.SingleProcessQueue()
    analysis_plugin = tagging.TaggingPlugin(event_queue)
    # pylint: disable=protected-access
    tags = analysis_plugin._ParseTaggingFile(
        self._GetTestFilePath([self.TEST_TAG_FILE_NAME]))
    self.assertEqual(len(tags), 2)
    self.assertIn(u'Application Execution', tags.keys())
    self.assertIn(u'File Downloaded', tags.keys())

  def TestTag(self):
    """Test that the tagging plugin successfully tags events."""
    event_queue = single_process.SingleProcessQueue()
    test_queue_producer = queue.ItemQueueProducer(event_queue)
    events = [self._CreateTestEventObject(test_event)
              for test_event
              in self.TEST_EVENTS]
    test_queue_producer.ProduceItems(events)
    analysis_plugin = tagging.TaggingPlugin(event_queue)
    test_file = self._GetTestFilePath([self.TEST_TAG_FILE_NAME])
    analysis_plugin.SetAndLoadTagFile(test_file)

    # Run the plugin.
    knowledge_base = self._SetUpKnowledgeBase()
    analysis_report_queue_consumer = self._RunAnalysisPlugin(
        analysis_plugin, knowledge_base)
    analysis_reports = self._GetAnalysisReportsFromQueue(
        analysis_report_queue_consumer)

    self.assertEqual(len(analysis_reports), 1)
    report = analysis_reports[0]
    self.assertEqual(len(report.GetTags()), 2)


if __name__ == '__main__':
  unittest.main()
