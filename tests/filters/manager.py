#!/usr/bin/python
# -*- coding: utf-8 -*-
"""Tests for the event filters manager."""

import unittest

from plaso.filters import manager

from tests.filters import test_lib


class FiltersManagerTest(unittest.TestCase):
  """Tests for the event filters manager."""

  def testFilterRegistration(self):
    """Tests the RegisterFilter and DeregisterFilter functions."""
    # pylint: disable=protected-access
    number_of_filters = len(manager.FiltersManager._filter_classes)

    manager.FiltersManager.RegisterFilter(test_lib.TestEventFilter)
    self.assertEqual(
        len(manager.FiltersManager._filter_classes),
        number_of_filters + 1)

    with self.assertRaises(KeyError):
      manager.FiltersManager.RegisterFilter(test_lib.TestEventFilter)

    manager.FiltersManager.DeregisterFilter(test_lib.TestEventFilter)
    self.assertEqual(
        len(manager.FiltersManager._filter_classes),
        number_of_filters)


if __name__ == '__main__':
  unittest.main()
