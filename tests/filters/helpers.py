#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""Tests for the event filter helper functions and classes."""

from __future__ import unicode_literals

import unittest

from plaso.filters import helpers

from tests import test_lib as shared_test_lib


# TODO: add tests for GetUnicodeString


class DateCompareObjectTest(shared_test_lib.BaseTestCase):
  """Tests the date comparison helper."""

  def testInitialize(self):
    """Tests the __init__ function."""
    date_compare_object = helpers.DateCompareObject(0)
    self.assertIsNotNone(date_compare_object)

  # TODO: improve test coverage


# TODO: add tests for DictObject
# TODO: add tests for TimeRangeCache


if __name__ == "__main__":
  unittest.main()
