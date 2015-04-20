#!/usr/bin/python
# -*- coding: utf-8 -*-
"""Tests the foreman class for monitoring workers."""

import unittest

from plaso.multi_processing import foreman


class ForemanTest(unittest.TestCase):
  """Tests the foreman object."""

  def testInitialization(self):
    """Tests the initialization."""
    # TODO: pass an event queue producer to the foreman instead of none.
    foreman_object = foreman.Foreman(None)
    self.assertNotEqual(foreman_object, None)

  # TODO: add more tests.


if __name__ == '__main__':
  unittest.main()
