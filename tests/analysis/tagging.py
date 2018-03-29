#!/usr/bin/env python
# -*- coding: utf-8 -*-
"""Tests for the tagging analysis plugin."""

from __future__ import unicode_literals

import os
import unittest

from plaso.analysis import tagging
from plaso.lib import errors
from plaso.lib import timelib
from plaso.containers import events

from tests import test_lib as shared_test_lib
from tests.analysis import test_lib


class TestPrefetchEvent(events.EventObject):
  """A test event type for the tagging analysis plugin."""
  DATA_TYPE = 'windows:prefetch'


class TestChromeDownloadEvent(events.EventObject):
  """A test event type for the tagging analysis plugin."""
  DATA_TYPE = 'chrome:history:file_downloaded'


class TestEvtRecordEvent(events.EventObject):
  """A test event type for the tagging analysis plugin."""
  DATA_TYPE = 'windows:evt:record'


class TaggingAnalysisPluginTest(test_lib.AnalysisPluginTestCase):
  """Tests the tagging analysis plugin."""

  # pylint: disable=protected-access

  _INVALID_TEST_TAG_FILE_NAME = os.path.join(
      'tagging_file', 'invalid_syntax.txt')
  _TEST_TAG_FILE_NAME = os.path.join('tagging_file', 'valid.txt')

  _TEST_EVENTS = [
      {'event_type': 'prefetch',
       'timestamp': timelib.Timestamp.CopyFromString('2015-05-01 15:12:00'),
       'attributes': {}
      },
      {'event_type': 'chrome_download',
       'timestamp': timelib.Timestamp.CopyFromString('2015-05-01 05:06:00'),
       'attributes': {}
      },
      {'event_type': 'something_else',
       'timestamp': timelib.Timestamp.CopyFromString('2015-02-19 08:00:01'),
       'attributes': {}
      },
      {'event_type': 'evt',
       'timestamp': timelib.Timestamp.CopyFromString('2016-05-25 13:00:06'),
       'attributes': {
           'source_name': 'Security',
           'event_identifier': 538}
      },
      {'event_type': 'evt',
       'timestamp': timelib.Timestamp.CopyFromString('2016-05-25 13:00:06'),
       'attributes': {
           'source_name': 'Messaging',
           'event_identifier': 16,
           'body': 'this is a message'}
      },
  ]

  # pylint: disable=arguments-differ
  def _CreateTestEventObject(self, event_attributes):
    """Create a test event with a set of attributes.

    Args:
      event_attributes (dict[str, str]): attributes of an event to add to the
          queue.

    Returns:
      EventObject: event with the appropriate attributes for testing.
    """
    if event_attributes['event_type'] == 'prefetch':
      event_object = TestPrefetchEvent()
    elif event_attributes['event_type'] == 'chrome_download':
      event_object = TestChromeDownloadEvent()
    elif event_attributes['event_type'] == 'evt':
      event_object = TestEvtRecordEvent()
    else:
      event_object = events.EventObject()

    event_object.timestamp = event_attributes['timestamp']
    for key, value in iter(event_attributes['attributes'].items()):
      setattr(event_object, key, value)
    return event_object

  @shared_test_lib.skipUnlessHasTestFile(['tagging_file', 'valid.txt'])
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
    self.assertEqual(storage_writer.number_of_event_tags, 4)

    report = storage_writer.analysis_reports[0]
    self.assertIsNotNone(report)

    expected_text = 'Tagging plugin produced 4 tags.\n'
    self.assertEqual(report.text, expected_text)

    labels = []
    for event_tag in storage_writer.GetEventTags():
      labels.extend(event_tag.labels)

    self.assertEqual(len(labels), 5)

    # This is from a tag rule declared in objectfilter syntax.
    self.assertIn('application_execution', labels)
    # This is from a tag rule declared in dotty syntax.
    self.assertIn('login_attempt', labels)
    # This is from a rule using the "contains" operator
    self.assertIn('text_contains', labels)

  @shared_test_lib.skipUnlessHasTestFile([
      'tagging_file', 'invalid_syntax.txt'])
  @shared_test_lib.skipUnlessHasTestFile(['tagging_file', 'valid.txt'])
  def testParseTaggingFile(self):
    """Tests the _ParseTaggingFile function."""
    plugin = tagging.TaggingAnalysisPlugin()
    test_path = self._GetTestFilePath([self._TEST_TAG_FILE_NAME])

    tag_expression = plugin._ParseTaggingFile(test_path)
    self.assertEqual(len(tag_expression.children), 5)

    plugin = tagging.TaggingAnalysisPlugin()

    test_path = self._GetTestFilePath([self._INVALID_TEST_TAG_FILE_NAME])

    with self.assertRaises(errors.TaggingFileError):
      plugin._ParseTaggingFile(test_path)


if __name__ == '__main__':
  unittest.main()
