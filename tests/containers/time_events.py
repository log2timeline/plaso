#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""Tests for the shell item event attribute container."""

import unittest

from dfdatetime import posix_time as dfdatetime_posix_time

from plaso.containers import time_events

from tests import test_lib as shared_test_lib


class DateTimeValuesEventTest(shared_test_lib.BaseTestCase):
  """Tests for the dfDateTime-based event attribute container."""

  def testGetAttributeNames(self):
    """Tests the GetAttributeNames function."""
    posix_time = dfdatetime_posix_time.PosixTime(timestamp=0)
    attribute_container = time_events.DateTimeValuesEvent(posix_time, 'usage')

    expected_attribute_names = [
        '_event_data_row_identifier',
        'date_time',
        'timestamp',
        'timestamp_desc']

    attribute_names = sorted(attribute_container.GetAttributeNames())

    self.assertEqual(attribute_names, expected_attribute_names)


if __name__ == '__main__':
  unittest.main()
