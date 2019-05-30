#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""Tests for the unique domains visited analysis plugin."""

from __future__ import unicode_literals

import unittest

from plaso.analysis import unique_domains_visited
from plaso.lib import definitions
from plaso.lib import timelib

from tests.analysis import test_lib


class UniqueDomainsPluginTest(test_lib.AnalysisPluginTestCase):
  """Tests for the unique domains analysis plugin."""

  _TEST_EVENTS = [
      {'data_type': 'chrome:history:file_downloaded',
       'domain':'firstevent.com',
       'path': '/1/index.html',
       'timestamp': timelib.Timestamp.CopyFromString('2015-01-01 01:00:00'),
       'timestamp_desc': definitions.TIME_DESCRIPTION_UNKNOWN,
       'url': 'https://firstevent.com/1/index.html'},
      {'data_type': 'firefox:places:page_visited',
       'domain': 'secondevent.net',
       'path': '/2/index.html',
       'timestamp': timelib.Timestamp.CopyFromString('2015-02-02 02:00:00'),
       'timestamp_desc': definitions.TIME_DESCRIPTION_UNKNOWN,
       'url': 'https://secondevent.net/2/index.html'},
      {'data_type': 'msiecf:redirected',
       'domain': 'thirdevent.org',
       'path': '/3/index.html',
       'timestamp': timelib.Timestamp.CopyFromString('2015-03-03 03:00:00'),
       'timestamp_desc': definitions.TIME_DESCRIPTION_UNKNOWN,
       'url': 'https://thirdevent.org/3/index.html'},
      {'data_type': 'safari:history:visit',
       'domain': 'fourthevent.co',
       'path': '/4/index.html',
       'timestamp': timelib.Timestamp.CopyFromString('2015-04-04 04:00:00'),
       'timestamp_desc': definitions.TIME_DESCRIPTION_UNKNOWN,
       'url': 'https://fourthevent.co/4/index.html'}]

  def testExamineEventAndCompileReport(self):
    """Tests the ExamineEvent and CompileReport functions."""
    plugin = unique_domains_visited.UniqueDomainsVisitedPlugin()
    storage_writer = self._AnalyzeEvents(self._TEST_EVENTS, plugin)

    self.assertEqual(len(storage_writer.analysis_reports), 1)

    analysis_report = storage_writer.analysis_reports[0]

    report_text = analysis_report.GetString()
    for event_dictionary in self._TEST_EVENTS:
      domain = event_dictionary.get('domain', '')
      self.assertIn(domain, report_text)


if __name__ == '__main__':
  unittest.main()
