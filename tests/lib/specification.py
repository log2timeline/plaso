#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""Tests for the format specification classes."""

import unittest

from plaso.lib import specification


class FormatSpecificationStoreTest(unittest.TestCase):
  """Class to test the specification store."""

  def testAddSpecification(self):
    """Function to test the AddSpecification function."""
    store = specification.FormatSpecificationStore()

    format_regf = specification.FormatSpecification('REGF')
    format_regf.AddNewSignature(b'regf', offset=0)

    format_esedb = specification.FormatSpecification('ESEDB')
    format_esedb.AddNewSignature(b'\xef\xcd\xab\x89', offset=4)

    store.AddSpecification(format_regf)
    store.AddSpecification(format_esedb)

    with self.assertRaises(KeyError):
      store.AddSpecification(format_regf)


if __name__ == '__main__':
  unittest.main()
