#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""Tests for the count related attribute containers."""

import unittest

from plaso.containers import counts

from tests import test_lib as shared_test_lib


class EventLabelCountTest(shared_test_lib.BaseTestCase):
  """Tests for the event label count attribute container."""

  def testGetAttributeNames(self):
    """Tests the GetAttributeNames function."""
    attribute_container = counts.EventLabelCount()

    expected_attribute_names = [
        'label',
        'number_of_events']

    attribute_names = sorted(attribute_container.GetAttributeNames())
    self.assertEqual(attribute_names, expected_attribute_names)


class ParserCountTest(shared_test_lib.BaseTestCase):
  """Tests for the parser count attribute container."""

  def testGetAttributeNames(self):
    """Tests the GetAttributeNames function."""
    attribute_container = counts.ParserCount()

    expected_attribute_names = [
        'name',
        'number_of_events']

    attribute_names = sorted(attribute_container.GetAttributeNames())
    self.assertEqual(attribute_names, expected_attribute_names)


if __name__ == '__main__':
  unittest.main()
