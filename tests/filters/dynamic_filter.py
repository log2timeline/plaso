#!/usr/bin/python
# -*- coding: utf-8 -*-
import unittest

from plaso.filters import dynamic_filter

from tests.filters import test_lib


class DynamicFilterTest(test_lib.FilterTestHelper):
  """Tests for the DynamicFilter filter."""

  def setUp(self):
    """Sets up the needed objects used throughout the test."""
    self.test_filter = dynamic_filter.DynamicFilter()

  def testFilterFail(self):
    """Run few tests that should not be a proper filter."""
    self.TestFail('/tmp/file_that_most_likely_does_not_exist')
    self.TestFail('some random stuff that is destined to fail')
    self.TestFail('some_stuff is "random" and other_stuff ')
    self.TestFail('some_stuff is "random" and other_stuff is not "random"')
    self.TestFail('SELECT stuff FROM machine WHERE conditions are met')
    self.TestFail('SELECT field_a, field_b WHERE ')
    self.TestFail('SELECT field_a, field_b SEPARATED BY')
    self.TestFail('SELECT field_a, SEPARATED BY field_b WHERE ')
    self.TestFail('SELECT field_a, field_b LIMIT WHERE')

  def testFilterApprove(self):
    self.TestTrue('SELECT stuff FROM machine WHERE some_stuff is "random"')
    self.TestTrue('SELECT field_a, field_b, field_c')
    self.TestTrue('SELECT field_a, field_b, field_c SEPARATED BY "%"')
    self.TestTrue('SELECT field_a, field_b, field_c LIMIT 10')
    self.TestTrue('SELECT field_a, field_b, field_c LIMIT 10 SEPARATED BY "|"')
    self.TestTrue('SELECT field_a, field_b, field_c SEPARATED BY "|" LIMIT 10')
    self.TestTrue('SELECT field_a, field_b, field_c WHERE date > "2012"')
    self.TestTrue(
        'SELECT field_a, field_b, field_c WHERE date > "2012" LIMIT 100')
    self.TestTrue((
        'SELECT field_a, field_b, field_c WHERE date > "2012" SEPARATED BY "@"'
        ' LIMIT 100'))
    self.TestTrue((
        'SELECT parser, date, time WHERE some_stuff is "random" and '
        'date < "2021-02-14 14:51:23"'))

  def testFilterFields(self):
    query = 'SELECT stuff FROM machine WHERE some_stuff is "random"'
    self.test_filter.CompileFilter(query)
    self.assertEqual(['stuff'], self.test_filter.fields)

    query = 'SELECT stuff, a, b, date FROM machine WHERE some_stuff is "random"'
    self.test_filter.CompileFilter(query)
    self.assertEqual(['stuff', 'a', 'b', 'date'], self.test_filter.fields)

    query = 'SELECT date, message, zone, hostname WHERE some_stuff is "random"'
    self.test_filter.CompileFilter(query)
    self.assertEqual(
        ['date', 'message', 'zone', 'hostname'], self.test_filter.fields)

    query = 'SELECT hlutir'
    self.test_filter.CompileFilter(query)
    self.assertEqual(['hlutir'], self.test_filter.fields)

    query = 'SELECT hlutir LIMIT 10'
    self.test_filter.CompileFilter(query)
    self.assertEqual(['hlutir'], self.test_filter.fields)
    self.assertEqual(10, self.test_filter.limit)


if __name__ == '__main__':
  unittest.main()
