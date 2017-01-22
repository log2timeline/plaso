#!/usr/bin/python
# -*- coding: utf-8 -*-
"""Tests for the tagging analysis plugin."""

import unittest

from plaso.analysis import tagging
from plaso.lib import timelib
from plaso.containers import events

from tests import test_lib as shared_test_lib
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
      {u'event_type': u'evt',
       u'timestamp': timelib.Timestamp.CopyFromString(u'2016-05-25 13:00:06'),
       u'attributes': {
           u'source_name': u'Messaging',
           u'event_identifier': 16,
           u'body': u'this is a message'}
      },
  ]

  def _CreateTestEventObject(self, event_attributes):
    """Create a test event with a set of attributes.

    Args:
      event_attributes (dict[str, str]): attributes of an event to add to the
          queue.

    Returns:
      EventObject: event with the appropriate attributes for testing.
    """
    if event_attributes[u'event_type'] == u'prefetch':
      event_object = TestPrefetchEvent()
    elif event_attributes[u'event_type'] == u'chrome_download':
      event_object = TestChromeDownloadEvent()
    elif event_attributes[u'event_type'] == u'evt':
      event_object = TestEvtRecordEvent()
    else:
      event_object = events.EventObject()

    event_object.timestamp = event_attributes[u'timestamp']
    for key, value in iter(event_attributes[u'attributes'].items()):
      setattr(event_object, key, value)
    return event_object

  @shared_test_lib.skipUnlessHasTestFile([u'test_tag_file.txt'])
  def testExamineEventAndCompileReport(self):
    """Tests the ExamineEvent and CompileReport functions."""
    test_events = []
    for event_dictionary in self._TEST_EVENTS:
      event = self._CreateTestEventObject(event_dictionary)
      test_events.append(event)

    test_file = self._GetTestFilePath([self._TEST_TAG_FILE_NAME])
    plugin = tagging.TaggingAnalysisPlugin()
    plugin.SetAndLoadTagFile(test_file)

    storage_writer = self._AnalyzeEvents(test_events, plugin)

    self.assertEqual(len(storage_writer.analysis_reports), 1)
    self.assertEqual(len(storage_writer.event_tags), 4)

    report = storage_writer.analysis_reports[0]
    self.assertIsNotNone(report)

    expected_text = u'Tagging plugin produced 4 tags.\n'
    self.assertEqual(report.text, expected_text)

    labels = []
    for event_tag in storage_writer.event_tags:
      labels.extend(event_tag.labels)

    self.assertEqual(len(labels), 5)

    # This is from a tag rule declared in objectfilter syntax.
    self.assertIn(u'application_execution', labels)
    # This is from a tag rule declared in dotty syntax.
    self.assertIn(u'login_attempt', labels)
    # This is from a rule using the "contains" operator
    self.assertIn(u'text_contains', labels)

  @shared_test_lib.skipUnlessHasTestFile([u'test_tag_file.txt'])
  @shared_test_lib.skipUnlessHasTestFile([u'invalid_test_tag_file.txt'])
  def testParseTaggingFile(self):
    """Tests the _ParseTaggingFile function."""
    plugin = tagging.TaggingAnalysisPlugin()
    test_path = self._GetTestFilePath([self._TEST_TAG_FILE_NAME])

    tag_expression = plugin._ParseTaggingFile(test_path)
    self.assertEqual(len(tag_expression.children), 5)

    plugin = tagging.TaggingAnalysisPlugin()
    test_path = self._GetTestFilePath([self._INVALID_TEST_TAG_FILE_NAME])

    tag_expression = plugin._ParseTaggingFile(test_path)
    self.assertEqual(len(tag_expression.children), 2)


if __name__ == '__main__':
  unittest.main()
