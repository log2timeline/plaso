#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""Tests for the analyzer result attribute container."""

import unittest

from plaso.containers import analyzer_result

from tests import test_lib as shared_test_lib


class AnalyzerResultTest(shared_test_lib.BaseTestCase):
  """Tests for the analyzer result attribute container."""

  def testGetAttributeNames(self):
    """Tests the GetAttributeNames function."""
    attribute_container = analyzer_result.AnalyzerResult()

    expected_attribute_names = [
        'analyzer_name', 'attribute_name', 'attribute_value']

    attribute_names = sorted(attribute_container.GetAttributeNames())

    self.assertEqual(attribute_names, expected_attribute_names)


if __name__ == '__main__':
  unittest.main()
