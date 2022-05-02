#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""Tests for the report attribute containers."""

import unittest

from plaso.containers import reports

from tests import test_lib as shared_test_lib


class AnalysisReportTest(shared_test_lib.BaseTestCase):
  """Tests for the analysis report attribute container."""

  def testGetAttributeNames(self):
    """Tests the GetAttributeNames function."""
    attribute_container = reports.AnalysisReport()

    expected_attribute_names = [
        'analysis_counter',
        'event_filter',
        'plugin_name',
        'text',
        'time_compiled']

    attribute_names = sorted(attribute_container.GetAttributeNames())

    self.assertEqual(attribute_names, expected_attribute_names)

  # TODO: add tests for CopyToDict
  # TODO: add tests for GetString


if __name__ == '__main__':
  unittest.main()
