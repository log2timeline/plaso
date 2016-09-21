#!/usr/bin/python
# -*- coding: utf-8 -*-
"""Tests for the shared library utils."""

import unittest

from plaso.lib import utils


class UtilsTestCase(unittest.TestCase):
  """The unit test for utils method collection."""

  def testIsText(self):
    """Tests the IsText function."""
    bytes_in = b'this is My Weird ASCII and non whatever string.'
    self.assertTrue(utils.IsText(bytes_in))

    bytes_in = u'Plaso Síar Og Raðar Þessu'
    self.assertTrue(utils.IsText(bytes_in))

    bytes_in = b'\x01\\62LSO\xFF'
    self.assertFalse(utils.IsText(bytes_in))

    bytes_in = b'T\x00h\x00i\x00s\x00\x20\x00'
    self.assertTrue(utils.IsText(bytes_in))

    bytes_in = b'Ascii\x00'
    self.assertTrue(utils.IsText(bytes_in))

    bytes_in = b'Ascii Open then...\x00\x99\x23'
    self.assertFalse(utils.IsText(bytes_in))


if __name__ == '__main__':
  unittest.main()
