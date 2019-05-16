#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""Tests for the event filter parser classes."""

from __future__ import unicode_literals

import unittest

from plaso.lib import errors
from plaso.lib import lexer
from plaso.lib import objectfilter

from tests import test_lib as shared_test_lib


class TestFilterImplementation(objectfilter.BaseFilterImplementation):
  """Filter implementation for testing."""

  AndFilter = objectfilter.AndFilter
  IdentityFilter = objectfilter.IdentityFilter


class TokenTest(shared_test_lib.BaseTestCase):
  """Tests the event filter parser token."""

  def testInitialize(self):
    """Tests the __init__ function."""
    token = lexer.Token('STRING', r'\\(.)', 'StringEscape', None)
    self.assertIsNotNone(token)


class ExpressionTest(shared_test_lib.BaseTestCase):
  """Tests the event filter parser expression."""

  def testAddArg(self):
    """Tests the AddArg function."""
    expression = lexer.Expression()

    expression.AddArg('argument1')

    with self.assertRaises(errors.ParseError):
      expression.AddArg('argument2')

  def testSetAttribute(self):
    """Tests the SetAttribute function."""
    expression = lexer.Expression()

    expression.SetAttribute('attribute')

  def testSetOperator(self):
    """Tests the SetOperator function."""
    expression = lexer.Expression()

    expression.SetOperator('=')


class BinaryExpressionTest(shared_test_lib.BaseTestCase):
  """Tests the event filter parser binary expression."""

  def testAddOperands(self):
    """Tests the AddOperands function."""
    expression = lexer.BinaryExpression(operator='and')
    left_hand_expression = lexer.Expression()
    right_hand_expression = lexer.Expression()

    expression.AddOperands(left_hand_expression, right_hand_expression)

    with self.assertRaises(errors.ParseError):
      expression.AddOperands(None, right_hand_expression)

    with self.assertRaises(errors.ParseError):
      expression.AddOperands(left_hand_expression, None)

  def testCompile(self):
    """Tests the Compile function."""
    expression = lexer.BinaryExpression(operator='and')

    expression.Compile(TestFilterImplementation)

    expression = lexer.BinaryExpression()

    with self.assertRaises(errors.ParseError):
      expression.Compile(TestFilterImplementation)


class IdentityExpressionTest(shared_test_lib.BaseTestCase):
  """Tests the event filter parser identify expression."""

  def testCompile(self):
    """Tests the Compile function."""
    expression = lexer.IdentityExpression()
    expression.Compile(TestFilterImplementation)


class SearchParserTest(shared_test_lib.BaseTestCase):
  """Tests the event filter parser."""

  # TODO: add tests for _CombineBinaryExpressions
  # TODO: add tests for _CombineParenthesis
  # TODO: add tests for BinaryOperator

  def testBracketClose(self):
    """Tests the BracketClose function."""
    parser = lexer.SearchParser()

    parser.BracketClose()

  def testBracketOpen(self):
    """Tests the BracketOpen function."""
    parser = lexer.SearchParser()

    parser.BracketOpen()

  def testClose(self):
    """Tests the Close function."""
    parser = lexer.SearchParser()

    with self.assertRaises(errors.ParseError):
      parser.Close()

  def testDefault(self):
    """Tests the Default function."""
    parser = lexer.SearchParser()

    parser.Default()

  def testCompile(self):
    """Tests the Compile function."""
    parser = lexer.SearchParser()

    result = parser.Empty()
    self.assertTrue(result)

  # TODO: add tests for Error

  def testFeed(self):
    """Tests the Feed function."""
    parser = lexer.SearchParser()

    parser.Feed('data')

  # TODO: add tests for InsertArg
  # TODO: add tests for NextToken
  # TODO: add tests for Parse
  # TODO: add tests for PopState
  # TODO: add tests for PushBack
  # TODO: add tests for PushState
  # TODO: add tests for Reduce
  # TODO: add tests for StringEscape

  def testStringFinish(self):
    """Tests the StringFinish function."""
    parser = lexer.SearchParser()

    state = parser.StringFinish()
    self.assertIsNone(state)

  def testStringInsert(self):
    """Tests the StringInsert function."""
    parser = lexer.SearchParser()

    parser.StringStart()
    parser.StringInsert(string='string')

  def testStringStart(self):
    """Tests the StringStart function."""
    parser = lexer.SearchParser()

    parser.StringStart()

  def testStoreAttribute(self):
    """Tests the StoreAttribute function."""
    parser = lexer.SearchParser()

    token = parser.StoreAttribute(string='attribute')
    self.assertEqual(token, 'OPERATOR')

  def testStoreOperator(self):
    """Tests the StoreOperator function."""
    parser = lexer.SearchParser()

    parser.StoreOperator(string='and')


if __name__ == "__main__":
  unittest.main()
