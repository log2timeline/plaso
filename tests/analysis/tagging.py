#!/usr/bin/python
# -*- coding: utf-8 -*-
"""Tests for the tagging analysis plugin."""

import unittest

from plaso.analysis import tagging
from plaso.engine import plaso_queue
from plaso.engine import single_process
from plaso.lib import timelib
from plaso.containers import events

from tests.analysis import test_lib


class TestPrefetchEvent(events.EventObject):
  """A test event type for the tagging analysis plugin."""
  DATA_TYPE = u'windows:prefetch'


class TestChromeDownloadEvent(events.EventObject):
  """A test event type for the tagging analysis plugin."""
  DATA_TYPE = u'chrome:history:file_downloaded'

class TestEvtRecordEvent(events.EventObject):
  """A test event type for the tagging analysis plugin."""
  DATA_TYPE = u'windows:evt:record'


class TaggingTest(test_lib.AnalysisPluginTestCase):
  """Test for the tagging analysis plugin."""
  _INVALID_TEST_TAG_FILE_NAME = u'invalid_test_tag_file.txt'
  _TEST_TAG_FILE_NAME = u'test_tag_file.txt'

  _EVENT_DICTS = [
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
      },
      {u'event_type': u'evt',
       u'timestamp': timelib.Timestamp.CopyFromString(u'2016-05-25 13:00:06'),
       u'attributes': {
           u'source_name': u'Security',
           u'event_identifier': 538}
      },
  ]

  def _CreateTestEventObject(self, test_event_dict):
    """Create a basic event object to test the plugin on."""
    if test_event_dict[u'event_type'] == u'prefetch':
      event_object = TestPrefetchEvent()
    elif test_event_dict[u'event_type'] == u'chrome_download':
      event_object = TestChromeDownloadEvent()
    elif test_event_dict[u'event_type'] == u'evt':
      event_object = TestEvtRecordEvent()
    else:
      event_object = events.EventObject()

    event_object.timestamp = test_event_dict[u'timestamp']
    for key, value in iter(test_event_dict[u'attributes'].items()):
      setattr(event_object, key, value)
    return event_object

  def testParseTagFile(self):
    """Test that the tagging plugin can parse a tag definition file."""
    event_queue = single_process.SingleProcessQueue()
    analysis_plugin = tagging.TaggingPlugin(event_queue)
    # pylint: disable=protected-access
    tag_expression = analysis_plugin._ParseTaggingFile(
        self._GetTestFilePath([self._TEST_TAG_FILE_NAME]))
    self.assertEqual(len(tag_expression.children), 3)

  def testInvalidTagParsing(self):
    """Test parsing of definition files that contain invalid directives."""
    event_queue = single_process.SingleProcessQueue()
    analysis_plugin = tagging.TaggingPlugin(event_queue)
    # pylint: disable=protected-access
    tag_expression = analysis_plugin._ParseTaggingFile(
        self._GetTestFilePath([self._INVALID_TEST_TAG_FILE_NAME]))
    self.assertEqual(len(tag_expression.children), 2)

  def testTag(self):
    """Test that the tagging plugin successfully tags events."""
    event_queue = single_process.SingleProcessQueue()
    test_queue_producer = plaso_queue.ItemQueueProducer(event_queue)
    event_objects = [
        self._CreateTestEventObject(test_event)
        for test_event in self._EVENT_DICTS]
    test_queue_producer.ProduceItems(event_objects)
    analysis_plugin = tagging.TaggingPlugin(event_queue)
    test_file = self._GetTestFilePath([self._TEST_TAG_FILE_NAME])
    analysis_plugin.SetAndLoadTagFile(test_file)

    # Run the plugin.
    knowledge_base = self._SetUpKnowledgeBase()
    analysis_report_queue_consumer = self._RunAnalysisPlugin(
        analysis_plugin, knowledge_base)
    analysis_reports = self._GetAnalysisReportsFromQueue(
        analysis_report_queue_consumer)

    self.assertEqual(len(analysis_reports), 1)
    report = analysis_reports[0]
    tags = report.GetTags()
    self.assertEqual(len(tags), 3)

    labels = []
    for tag in tags:
      for label in tag.labels:
        labels.append(label)
    # This is from a tag rule declared in objectfilter syntax.
    self.assertIn(u'application_execution', labels)
    # This is from a tag rule declared in dotty syntax.
    self.assertIn(u'login_attempt', labels)


if __name__ == '__main__':
  unittest.main()
