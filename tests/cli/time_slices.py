#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""Tests for the time slice."""

import unittest

from plaso.cli import time_slices

from tests import test_lib as shared_test_lib


class TimeSliceTest(shared_test_lib.BaseTestCase):
  """Tests for the time slice."""

  def testInitialization(self):
    """Tests the __init__ function."""
    event_timestamp = 1467835655123456
    time_slice = time_slices.TimeSlice(event_timestamp)

    self.assertEqual(time_slice.event_timestamp, event_timestamp)
    self.assertEqual(time_slice.duration, 5)
    self.assertEqual(time_slice.end_timestamp, 1467835955123456)
    self.assertEqual(time_slice.start_timestamp, 1467835355123456)

    calculated_duration, _ = divmod(
        time_slice.end_timestamp - event_timestamp, 60 * 1000000)
    self.assertEqual(calculated_duration, 5)

    calculated_duration, _ = divmod(
        event_timestamp - time_slice.start_timestamp, 60 * 1000000)
    self.assertEqual(calculated_duration, 5)


if __name__ == '__main__':
  unittest.main()
