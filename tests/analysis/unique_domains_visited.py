#!/usr/bin/python
# -*- coding: utf-8 -*-
"""Tests for the unique domains visited analysis plugin."""

import unittest

from plaso.analysis import unique_domains_visited
from plaso.containers import events
from plaso.engine import plaso_queue
from plaso.engine import single_process
from plaso.lib import timelib

from tests.analysis import test_lib


class UniqueDomainsPluginTest(test_lib.AnalysisPluginTestCase):
  """Tests for the unique domains analysis plugin."""
  _EVENT_DICTS = [
      {u'data_type': u'chrome:history:file_downloaded',
       u'domain':u'firstevent.com',
       u'path': u'/1/index.html',
       u'timestamp': timelib.Timestamp.CopyFromString(u'2015-01-01 01:00:00')},
      {u'data_type': u'firefox:places:page_visited',
       u'domain': u'secondevent.net',
       u'path': u'/2/index.html',
       u'timestamp': timelib.Timestamp.CopyFromString(u'2015-02-02 02:00:00')},
      {u'data_type': u'msiecf:redirected',
       u'domain': u'thirdevent.org',
       u'path': u'/3/index.html',
       u'timestamp': timelib.Timestamp.CopyFromString(u'2015-03-03 03:00:00')},
      {u'data_type': u'safari:history:visit',
       u'domain': u'fourthevent.co',
       u'path': u'/4/index.html',
       u'timestamp': timelib.Timestamp.CopyFromString(u'2015-04-04 04:00:00')},
      ]

  def _CreateTestEventObject(self, test_event):
    """Create a test event object with a particular path.

    Args:
      test_event_dict: A dict containing attributes of an event to add to the
                       queue.

    Returns:
      An event object (instance of EventObject) that contains the necessary
      attributes for testing.
    """
    event_object = events.EventObject()
    event_object.data_type = test_event[u'data_type']
    event_object.url = u'https://{0:s}/{1:s}'.format(
        test_event.get(u'domain', u''), test_event.get(u'path', u''))
    event_object.timestamp = test_event[u'timestamp']
    return event_object

  def testUniqueDomainExtraction(self):
    """Tests for the unique domains plugin."""
    event_queue = single_process.SingleProcessQueue()
    knowledge_base = self._SetUpKnowledgeBase()

    # Fill the incoming queue with events.
    test_queue_producer = plaso_queue.ItemQueueProducer(event_queue)
    event_objects = [
        self._CreateTestEventObject(test_event)
        for test_event in self._EVENT_DICTS]
    test_queue_producer.ProduceItems(event_objects)

    # Set up the plugin.
    analysis_plugin = unique_domains_visited.UniqueDomainsVisitedPlugin(
        event_queue)

    analysis_report_queue_consumer = self._RunAnalysisPlugin(
        analysis_plugin, knowledge_base)
    analysis_reports = self._GetAnalysisReportsFromQueue(
        analysis_report_queue_consumer)

    self.assertEqual(len(analysis_reports), 1)
    report_text = analysis_reports[0].GetString()
    for event_object in self._EVENT_DICTS:
      self.assertIn(event_object.get(u'domain', u''), report_text)


if __name__ == '__main__':
  unittest.main()
