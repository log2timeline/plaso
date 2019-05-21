#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""Tests for the event filter expression parser filter classes."""

from __future__ import unicode_literals

import unittest

from plaso.filters import filters

from tests import test_lib as shared_test_lib


# TODO: add tests for Filter


class AndFilterTest(shared_test_lib.BaseTestCase):
  """Tests the boolean AND filter."""

  def testMatches(self):
    """Tests the Matches function."""
    filter_object = filters.AndFilter()

    result = filter_object.Matches(1)
    self.assertTrue(result)

    # TODO: add tests for filter with arguments.


class OrFilterTest(shared_test_lib.BaseTestCase):
  """Tests the boolean OR filter."""

  def testMatches(self):
    """Tests the Matches function."""
    filter_object = filters.OrFilter()

    result = filter_object.Matches(1)
    self.assertTrue(result)

    # TODO: add tests for filter with arguments.


# TODO: add tests for Operator
# TODO: add tests for IdentityFilter
# TODO: add tests for BinaryOperator
# TODO: add tests for GenericBinaryOperator


class EqualsOperatorTest(shared_test_lib.BaseTestCase):
  """Tests the equals operator."""

  def testOperation(self):
    """Tests the Operation function."""
    filter_object = filters.EqualsOperator(arguments=['first', 'second'])

    result = filter_object.Operation(0, 10)
    self.assertFalse(result)

    result = filter_object.Operation(10, 10)
    self.assertTrue(result)


class NotEqualsOperatorTest(shared_test_lib.BaseTestCase):
  """Tests the not equals operator."""

  def testOperation(self):
    """Tests the Operation function."""
    filter_object = filters.NotEqualsOperator(arguments=['first', 'second'])

    result = filter_object.Operation(0, 10)
    self.assertTrue(result)

    result = filter_object.Operation(10, 10)
    self.assertFalse(result)


class LessThanOperatorTest(shared_test_lib.BaseTestCase):
  """Tests the less than operator."""

  def testOperation(self):
    """Tests the Operation function."""
    filter_object = filters.LessThanOperator(arguments=['first', 'second'])

    result = filter_object.Operation(0, 10)
    self.assertTrue(result)

    result = filter_object.Operation(10, 10)
    self.assertFalse(result)

    result = filter_object.Operation(20, 10)
    self.assertFalse(result)


class LessEqualOperatorTest(shared_test_lib.BaseTestCase):
  """Tests the less equal operator."""

  def testOperation(self):
    """Tests the Operation function."""
    filter_object = filters.LessEqualOperator(arguments=['first', 'second'])

    result = filter_object.Operation(0, 10)
    self.assertTrue(result)

    result = filter_object.Operation(10, 10)
    self.assertTrue(result)

    result = filter_object.Operation(20, 10)
    self.assertFalse(result)


class GreaterThanOperatorTest(shared_test_lib.BaseTestCase):
  """Tests the greater than operator."""

  def testOperation(self):
    """Tests the Operation function."""
    filter_object = filters.GreaterThanOperator(arguments=['first', 'second'])

    result = filter_object.Operation(0, 10)
    self.assertFalse(result)

    result = filter_object.Operation(10, 10)
    self.assertFalse(result)

    result = filter_object.Operation(20, 10)
    self.assertTrue(result)


class GreaterEqualOperatorTest(shared_test_lib.BaseTestCase):
  """Tests the greater equal operator."""

  def testOperation(self):
    """Tests the Operation function."""
    filter_object = filters.GreaterEqualOperator(arguments=['first', 'second'])

    result = filter_object.Operation(0, 10)
    self.assertFalse(result)

    result = filter_object.Operation(10, 10)
    self.assertTrue(result)

    result = filter_object.Operation(20, 10)
    self.assertTrue(result)


# TODO: add tests for Contains
# TODO: add tests for InSet
# TODO: add tests for Regexp
# TODO: add tests for RegexpInsensitive
# TODO: add tests for ContextOperator


if __name__ == "__main__":
  unittest.main()
