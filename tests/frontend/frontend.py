#!/usr/bin/python
# -*- coding: utf-8 -*-
"""Tests for the front-end."""

import unittest

from plaso.frontend import frontend

from tests import test_lib as shared_test_lib


class TimeSliceTest(shared_test_lib.BaseTestCase):
  """Tests for the date time file entry filter."""

  def testInitialization(self):
    """Tests the object initialization function."""
    event_timestamp = 1467835655123456
    time_slice = frontend.TimeSlice(event_timestamp)

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
