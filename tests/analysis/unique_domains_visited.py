#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""Tests for the unique domains visited analysis plugin."""

import unittest

from plaso.analysis import unique_domains_visited
from plaso.containers import reports
from plaso.lib import definitions

from tests.analysis import test_lib


class UniqueDomainsPluginTest(test_lib.AnalysisPluginTestCase):
  """Tests for the unique domains analysis plugin."""

  _TEST_EVENTS = [
      {'_parser_chain': 'sqlite/chrome_history',
       'data_type': 'chrome:history:file_downloaded',
       'domain': 'firstevent.com',
       'path': '/1/index.html',
       'timestamp': '2015-01-01 01:00:00',
       'timestamp_desc': definitions.TIME_DESCRIPTION_UNKNOWN,
       'url': 'https://firstevent.com/1/index.html'},
      {'_parser_chain': 'sqlite/firefox_history',
       'data_type': 'firefox:places:page_visited',
       'domain': 'secondevent.net',
       'path': '/2/index.html',
       'timestamp': '2015-02-02 02:00:00',
       'timestamp_desc': definitions.TIME_DESCRIPTION_UNKNOWN,
       'url': 'https://secondevent.net/2/index.html'},
      {'_parser_chain': 'msiecf',
       'data_type': 'msiecf:redirected',
       'domain': 'thirdevent.org',
       'path': '/3/index.html',
       'timestamp': '2015-03-03 03:00:00',
       'timestamp_desc': definitions.TIME_DESCRIPTION_UNKNOWN,
       'url': 'https://thirdevent.org/3/index.html'},
      {'_parser_chain': 'safari_history',
       'data_type': 'safari:history:visit',
       'domain': 'fourthevent.co',
       'path': '/4/index.html',
       'timestamp': '2015-04-04 04:00:00',
       'timestamp_desc': definitions.TIME_DESCRIPTION_UNKNOWN,
       'url': 'https://fourthevent.co/4/index.html'}]

  def testExamineEventAndCompileReport(self):
    """Tests the ExamineEvent and CompileReport functions."""
    plugin = unique_domains_visited.UniqueDomainsVisitedPlugin()
    storage_writer = self._AnalyzeEvents(self._TEST_EVENTS, plugin)

    number_of_reports = storage_writer.GetNumberOfAttributeContainers(
        'analysis_report')
    self.assertEqual(number_of_reports, 1)

    analysis_report = storage_writer.GetAttributeContainerByIndex(
        reports.AnalysisReport.CONTAINER_TYPE, 0)

    self.assertEqual(analysis_report.analysis_counter['firstevent.com'], 1)
    self.assertEqual(analysis_report.analysis_counter['secondevent.net'], 1)
    self.assertEqual(analysis_report.analysis_counter['thirdevent.org'], 1)
    self.assertEqual(analysis_report.analysis_counter['fourthevent.co'], 1)


if __name__ == '__main__':
  unittest.main()
