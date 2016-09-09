#!/usr/bin/python
# -*- coding: utf-8 -*-
"""Tests for the unique domains visited analysis plugin."""

import unittest

from plaso.analysis import unique_domains_visited
from plaso.lib import timelib

from tests.analysis import test_lib


class UniqueDomainsPluginTest(test_lib.AnalysisPluginTestCase):
  """Tests for the unique domains analysis plugin."""

  _TEST_EVENTS = [
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

  def testExamineEventAndCompileReport(self):
    """Tests the ExamineEvent and CompileReport functions."""
    events = []
    for event_dictionary in self._TEST_EVENTS:
      event_dictionary[u'url'] = u'https://{0:s}/{1:s}'.format(
          event_dictionary[u'domain'], event_dictionary[u'path'])

      event = self._CreateTestEventObject(event_dictionary)
      events.append(event)

    plugin = unique_domains_visited.UniqueDomainsVisitedPlugin()
    storage_writer = self._AnalyzeEvents(events, plugin)

    self.assertEqual(len(storage_writer.analysis_reports), 1)

    analysis_report = storage_writer.analysis_reports[0]

    report_text = analysis_report.GetString()
    for event_dictionary in self._TEST_EVENTS:
      domain = event_dictionary.get(u'domain', u'')
      self.assertIn(domain, report_text)


if __name__ == '__main__':
  unittest.main()
