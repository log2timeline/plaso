#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""Tests for the collection filters helper."""

from __future__ import unicode_literals

import unittest

from plaso.engine import filters_helper

from tests import test_lib as shared_test_lib


class CollectionFiltersHelperTest(shared_test_lib.BaseTestCase):
  """Tests for the collection filters helper."""

  def testInitialize(self):
    """Tests the __init__ function."""
    test_helper = filters_helper.CollectionFiltersHelper()
    self.assertIsNotNone(test_helper)


if __name__ == '__main__':
  unittest.main()
