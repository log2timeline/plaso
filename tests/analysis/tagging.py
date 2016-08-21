#!/usr/bin/python
# -*- coding: utf-8 -*-
"""Tests for the tagging analysis plugin."""

import unittest

from plaso.analysis import tagging
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


class TaggingAnalysisPluginTest(test_lib.AnalysisPluginTestCase):
  """Tests the tagging analysis plugin."""

  # pylint: disable=protected-access

  _INVALID_TEST_TAG_FILE_NAME = u'invalid_test_tag_file.txt'
  _TEST_TAG_FILE_NAME = u'test_tag_file.txt'

  _TEST_EVENTS = [
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
    """Create a test event with a set of attributes.

    Args:
      event_dictionary (dict[str, str]): contains attributes of an event to add
          to the queue.

    Returns:
      EventObject: event with the appropriate attributes for testing.
    """
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

  def testParseTaggingFile(self):
    """Tests the _ParseTaggingFile function."""
    plugin = tagging.TaggingAnalysisPlugin()
    test_path = self._GetTestFilePath([self._TEST_TAG_FILE_NAME])

    tag_expression = plugin._ParseTaggingFile(test_path)
    self.assertEqual(len(tag_expression.children), 4)

    plugin = tagging.TaggingAnalysisPlugin()
    test_path = self._GetTestFilePath([self._INVALID_TEST_TAG_FILE_NAME])

    tag_expression = plugin._ParseTaggingFile(test_path)
    self.assertEqual(len(tag_expression.children), 2)

  def testExamineEventAndCompileReport(self):
    """Tests the ExamineEvent and CompileReport functions."""
    event_objects = []
    for event_dictionary in self._TEST_EVENTS:
      event = self._CreateTestEventObject(event_dictionary)
      event_objects.append(event)

    test_file = self._GetTestFilePath([self._TEST_TAG_FILE_NAME])
    plugin = tagging.TaggingAnalysisPlugin()
    plugin.SetAndLoadTagFile(test_file)

    storage_writer = self._AnalyzeEvents(event_objects, plugin)

    self.assertEqual(len(storage_writer.analysis_reports), 1)

    analysis_report = storage_writer.analysis_reports[0]

    tags = analysis_report.GetTags()
    self.assertEqual(len(tags), 3)

    labels = []
    for tag in tags:
      labels.extend(tag.labels)
    self.assertEqual(len(labels), 4)

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
