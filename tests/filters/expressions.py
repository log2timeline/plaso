#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""Tests for the event filter expression parser expression classes."""

import unittest

from plaso.filters import expressions
from plaso.lib import errors

from tests import test_lib as shared_test_lib


class ExpressionTest(shared_test_lib.BaseTestCase):
  """Tests the expression."""

  def testAddArgument(self):
    """Tests the AddArgument function."""
    expression = expressions.Expression()

    expression.AddArgument('argument1')

    with self.assertRaises(errors.ParseError):
      expression.AddArgument('argument2')

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

  def testCompile(self):
    """Tests the Compile function."""
    expression = expressions.EventExpression()
    expression.SetOperator('==')
    expression.AddArgument('first')
    expression.Compile()

    # Test missing operator.
    expression = expressions.EventExpression()
    expression.AddArgument('first')
    with self.assertRaises(errors.ParseError):
      expression.Compile()

    # Test unknown operator.
    expression = expressions.EventExpression()
    expression.SetOperator('bogus')
    expression.AddArgument('first')
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
