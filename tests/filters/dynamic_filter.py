#!/usr/bin/env python
# -*- coding: utf-8 -*-
"""Tests for the dynamic event object filter."""

from __future__ import unicode_literals

import unittest

from plaso.filters import dynamic_filter
from plaso.lib import errors

from tests.filters import test_lib


class DynamicFilterTest(test_lib.FilterTestCase):
  """Tests for the DynamicFilter filter."""

  def testCompilerFilter(self):
    """Tests the CompileFilter function."""
    test_filter = dynamic_filter.DynamicFilter()

    test_filter.CompileFilter(
        'SELECT stuff FROM machine WHERE some_stuff is "random"')

    test_filter.CompileFilter(
        'SELECT field_a, field_b, field_c')

    test_filter.CompileFilter(
        'SELECT field_a, field_b, field_c SEPARATED BY "%"')

    test_filter.CompileFilter(
        'SELECT field_a, field_b, field_c LIMIT 10')

    test_filter.CompileFilter(
        'SELECT field_a, field_b, field_c LIMIT 10 SEPARATED BY "|"')

    test_filter.CompileFilter(
        'SELECT field_a, field_b, field_c SEPARATED BY "|" LIMIT 10')

    test_filter.CompileFilter(
        'SELECT field_a, field_b, field_c WHERE date > "2012"')

    test_filter.CompileFilter(
        'SELECT field_a, field_b, field_c WHERE date > "2012" LIMIT 100')

    test_filter.CompileFilter((
        'SELECT field_a, field_b, field_c WHERE date > "2012" SEPARATED BY '
        '"@" LIMIT 100'))

    test_filter.CompileFilter((
        'SELECT parser, date, time WHERE some_stuff is "random" and '
        'date < "2021-02-14 14:51:23"'))

    with self.assertRaises(errors.WrongPlugin):
      test_filter.CompileFilter(
          '/tmp/file_that_most_likely_does_not_exist')

    with self.assertRaises(errors.WrongPlugin):
      test_filter.CompileFilter(
          'some random stuff that is destined to fail')

    with self.assertRaises(errors.WrongPlugin):
      test_filter.CompileFilter(
          'some_stuff is "random" and other_stuff ')

    with self.assertRaises(errors.WrongPlugin):
      test_filter.CompileFilter(
          'some_stuff is "random" and other_stuff is not "random"')

    with self.assertRaises(errors.WrongPlugin):
      test_filter.CompileFilter(
          'SELECT stuff FROM machine WHERE conditions are met')

    with self.assertRaises(errors.WrongPlugin):
      test_filter.CompileFilter('SELECT field_a, field_b WHERE ')

    with self.assertRaises(errors.WrongPlugin):
      test_filter.CompileFilter('SELECT field_a, field_b SEPARATED BY')

    with self.assertRaises(errors.WrongPlugin):
      test_filter.CompileFilter('SELECT field_a, SEPARATED BY field_b WHERE ')

    with self.assertRaises(errors.WrongPlugin):
      test_filter.CompileFilter('SELECT field_a, field_b LIMIT WHERE')

  def testFields(self):
    """Tests the fields property."""
    test_filter = dynamic_filter.DynamicFilter()

    test_filter.CompileFilter(
        'SELECT stuff FROM machine WHERE some_stuff is "random"')
    expected_fields = ['stuff']
    self.assertEqual(test_filter.fields, expected_fields)

    test_filter.CompileFilter(
        'SELECT stuff, a, b, date FROM machine WHERE some_stuff is "random"')
    expected_fields = ['stuff', 'a', 'b', 'date']
    self.assertEqual(test_filter.fields, expected_fields)

    test_filter.CompileFilter(
        'SELECT date, message, zone, hostname WHERE some_stuff is "random"')
    expected_fields = ['date', 'message', 'zone', 'hostname']
    self.assertEqual(test_filter.fields, expected_fields)

    test_filter.CompileFilter('SELECT hlutir')
    expected_fields = ['hlutir']
    self.assertEqual(test_filter.fields, expected_fields)

    test_filter.CompileFilter('SELECT hlutir LIMIT 10')
    expected_fields = ['hlutir']
    self.assertEqual(test_filter.fields, expected_fields)
    self.assertEqual(10, test_filter.limit)


if __name__ == '__main__':
  unittest.main()
