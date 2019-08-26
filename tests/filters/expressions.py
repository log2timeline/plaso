#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""Tests for the event filter expression parser expression classes."""

from __future__ import unicode_literals

import unittest

from plaso.filters import expressions
from plaso.lib import errors

from tests import test_lib as shared_test_lib


class ExpressionTest(shared_test_lib.BaseTestCase):
  """Tests the expression."""

  def testAddArg(self):
    """Tests the AddArg function."""
    expression = expressions.Expression()

    expression.AddArg('argument1')

    with self.assertRaises(errors.ParseError):
      expression.AddArg('argument2')

  def testSetAttribute(self):
    """Tests the SetAttribute function."""
    expression = expressions.Expression()

    expression.SetAttribute('attribute')

  def testSetOperator(self):
    """Tests the SetOperator function."""
    expression = expressions.Expression()

    expression.SetOperator('==')


class BinaryExpressionTest(shared_test_lib.BaseTestCase):
  """Tests the binary expression."""

  def testAddOperands(self):
    """Tests the AddOperands function."""
    expression = expressions.BinaryExpression(operator='and')
    left_hand_expression = expressions.Expression()
    right_hand_expression = expressions.Expression()

    expression.AddOperands(left_hand_expression, right_hand_expression)

    with self.assertRaises(errors.ParseError):
      expression.AddOperands(None, right_hand_expression)

    with self.assertRaises(errors.ParseError):
      expression.AddOperands(left_hand_expression, None)

  def testCompile(self):
    """Tests the Compile function."""
    expression = expressions.BinaryExpression(operator='and')

    expression.Compile()

    expression = expressions.BinaryExpression()

    with self.assertRaises(errors.ParseError):
      expression.Compile()


class IdentityExpressionTest(shared_test_lib.BaseTestCase):
  """Tests identity expression."""

  def testCompile(self):
    """Tests the Compile function."""
    expression = expressions.IdentityExpression()
    expression.Compile()


class EventExpressionTest(shared_test_lib.BaseTestCase):
  """Tests the event expression."""

  # pylint: disable=protected-access

  def testCopyValueToDateTime(self):
    """Tests the _CopyValueToDateTime function."""
    expression = expressions.EventExpression()

    date_time = expression._CopyValueToDateTime('2009-07-13T23:29:02.849131')
    self.assertIsNotNone(date_time)
    self.assertEqual(date_time.timestamp, 1247527742849131)

    date_time = expression._CopyValueToDateTime('2009-07-13')
    self.assertIsNotNone(date_time)
    self.assertEqual(date_time.timestamp, 1247443200000000)

    date_time = expression._CopyValueToDateTime('2009-07-13 23:29:02')
    self.assertIsNotNone(date_time)
    self.assertEqual(date_time.timestamp, 1247527742000000)

    date_time = expression._CopyValueToDateTime('2009-07-13 23:29:02.849131')
    self.assertIsNotNone(date_time)
    self.assertEqual(date_time.timestamp, 1247527742849131)

    date_time = expression._CopyValueToDateTime('1247527742849131')
    self.assertIsNotNone(date_time)
    self.assertEqual(date_time.timestamp, 1247527742849131)

    date_time = expression._CopyValueToDateTime(1247527742849131)
    self.assertIsNotNone(date_time)
    self.assertEqual(date_time.timestamp, 1247527742849131)

    with self.assertRaises(ValueError):
      expression._CopyValueToDateTime(None)

  def testCompile(self):
    """Tests the Compile function."""
    expression = expressions.EventExpression()
    expression.SetOperator('==')
    expression.AddArg('first')
    expression.Compile()

    # Test missing operator.
    expression = expressions.EventExpression()
    expression.AddArg('first')
    with self.assertRaises(errors.ParseError):
      expression.Compile()

    # Test unknown operator.
    expression = expressions.EventExpression()
    expression.SetOperator('bogus')
    expression.AddArg('first')
    with self.assertRaises(errors.ParseError):
      expression.Compile()

    # Test missing arguments.
    expression = expressions.EventExpression()
    expression.SetOperator('==')
    with self.assertRaises(errors.InvalidNumberOfOperands):
      expression.Compile()

  def testNegate(self):
    """Tests the Negate function."""
    expression = expressions.EventExpression()
    self.assertTrue(expression._bool_value)

    expression.Negate()
    self.assertFalse(expression._bool_value)


if __name__ == "__main__":
  unittest.main()
