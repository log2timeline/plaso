#!/usr/bin/python
# -*- coding: utf-8 -*-
"""This file contains the tests for the report attribute containers."""

import unittest

from plaso.containers import reports

from tests import test_lib as shared_test_lib


class AnalysisReportTest(shared_test_lib.BaseTestCase):
  """Tests for the analysis report attributes container."""

  def testCopyToDict(self):
    """Tests the CopyToDict function."""
    analysis_report = reports.AnalysisReport(
        plugin_name=u'test', text=u'This is a test analysis report')

    expected_dict = {
        u'plugin_name': u'test',
        u'text': u'This is a test analysis report'}

    test_dict = analysis_report.CopyToDict()

    self.assertEqual(test_dict, expected_dict)

  # TODO: add more tests.


if __name__ == '__main__':
  unittest.main()
