#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""Tests for the event filter expression parser expression classes."""

import unittest

from plaso.filters import value_types

from tests import test_lib as shared_test_lib


class DateTimeValueTypeTest(shared_test_lib.BaseTestCase):
  """Tests the date and time value type."""

  def testInitialize(self):
    """Tests the __init__ function."""
    date_time = value_types.DateTimeValueType('2009-07-13T23:29:02.849131')
    self.assertIsNotNone(date_time)
    self.assertEqual(date_time.timestamp, 1247527742849131)

    date_time = value_types.DateTimeValueType('2009-07-13')
    self.assertIsNotNone(date_time)
    self.assertEqual(date_time.timestamp, 1247443200000000)

    date_time = value_types.DateTimeValueType('2009-07-13 23:29:02')
    self.assertIsNotNone(date_time)
    self.assertEqual(date_time.timestamp, 1247527742000000)

    date_time = value_types.DateTimeValueType('2009-07-13 23:29:02.849131')
    self.assertIsNotNone(date_time)
    self.assertEqual(date_time.timestamp, 1247527742849131)

    date_time = value_types.DateTimeValueType('1247527742849131')
    self.assertIsNotNone(date_time)
    self.assertEqual(date_time.timestamp, 1247527742849131)

    date_time = value_types.DateTimeValueType(1247527742849131)
    self.assertIsNotNone(date_time)
    self.assertEqual(date_time.timestamp, 1247527742849131)

    with self.assertRaises(ValueError):
      value_types.DateTimeValueType(None)


if __name__ == "__main__":
  unittest.main()
