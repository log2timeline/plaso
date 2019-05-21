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


class ContextExpressionTest(shared_test_lib.BaseTestCase):
  """Tests the context expression."""

  def testCompile(self):
    """Tests the Compile function."""
    # TODO: add successful test.

    # Test missing arguments.
    expression = expressions.ContextExpression()
    with self.assertRaises(errors.InvalidNumberOfOperands):
      expression.Compile()

  def testSetExpression(self):
    """Tests the SetExpression function."""
    expression = expressions.ContextExpression()

    test_expression = expressions.Expression()
    expression.SetExpression(test_expression)

    with self.assertRaises(errors.ParseError):
      expression.SetExpression('bogus')


class EventExpressionTest(shared_test_lib.BaseTestCase):
  """Tests the event expression."""

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

  def testFlipBool(self):
    """Tests the FlipBool function."""
    expression = expressions.EventExpression()
    self.assertTrue(expression.bool_value)

    expression.FlipBool()
    self.assertFalse(expression.bool_value)


if __name__ == "__main__":
  unittest.main()
