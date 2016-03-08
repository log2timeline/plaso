#!/usr/bin/python
# -*- coding: utf-8 -*-
"""This file contains the tests for the report attribute container objects."""

import unittest

from plaso.containers import reports

from tests.containers import test_lib


class AnalysisReportTest(test_lib.AttributeContainerTestCase):
  """Tests for the analysis report attributes container object."""

  def testCopyToDict(self):
    """Tests the CopyToDict function."""
    event_tag = reports.AnalysisReport(
        u'test', text=u'This is a test analysis report')

    expected_dict = {
        u'_event_tags': [],
        u'plugin_name': u'test',
        u'text': u'This is a test analysis report'}

    test_dict = event_tag.CopyToDict()

    self.assertEqual(test_dict, expected_dict)

  # TODO: add more tests.


if __name__ == '__main__':
  unittest.main()
