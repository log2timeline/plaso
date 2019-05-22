#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""Tests for the event filter functions."""

from __future__ import unicode_literals

import re
import unittest

from plaso.containers import events
from plaso.filters import expression_parser
from plaso.filters import filters
from plaso.formatters import interface as formatters_interface
from plaso.formatters import manager as formatters_manager
from plaso.lib import errors
from plaso.lib import timelib

from tests import test_lib as shared_test_lib
from tests.filters import test_lib


class PfilterFakeFormatter(formatters_interface.EventFormatter):
  """A formatter for this fake class."""
  DATA_TYPE = 'Weirdo:Made up Source:Last Written'

  FORMAT_STRING = '{text}'
  FORMAT_STRING_SHORT = '{text_short}'

  SOURCE_LONG = 'Fake Parsing Source'
  SOURCE_SHORT = 'REG'


formatters_manager.FormattersManager.RegisterFormatter(PfilterFakeFormatter)


class TokenTest(shared_test_lib.BaseTestCase):
  """Tests the event filter parser token."""

  def testInitialize(self):
    """Tests the __init__ function."""
    token = expression_parser.Token('STRING', r'\\(.)', 'StringEscape', None)
    self.assertIsNotNone(token)


class EventFilterExpressionParserTest(shared_test_lib.BaseTestCase):
  """Tests the event filter expression parser."""

  # pylint: disable=protected-access

  def _CheckFilterEvent(self, event, expression, expected_result):
    """Check if the expression filters the event.

    Args:
      event (EventObject): event.
      expression (str): event filter expression.
      expected_result (bool): expected result.
    """
    parser = expression_parser.EventFilterExpressionParser()
    expression = parser.Parse(expression)
    event_filter = expression.Compile()

    result = event_filter.Matches(event)
    self.assertEqual(expected_result, result)

  def testAddBinaryOperator(self):
    """Tests the _AddBinaryOperator function."""
    parser = expression_parser.EventFilterExpressionParser()
    parser._Reset()

    next_state = parser._AddBinaryOperator(string='&&')
    self.assertIsNone(next_state)
    self.assertIsNotNone(parser._stack[0])

  def testAddBracketClose(self):
    """Tests the _AddBracketClose function."""
    parser = expression_parser.EventFilterExpressionParser()
    parser._Reset()

    next_state = parser._AddBracketClose()
    self.assertIsNone(next_state)
    self.assertEqual(parser._stack[0], ')')

  def testAddBracketOpen(self):
    """Tests the _AddBracketOpen function."""
    parser = expression_parser.EventFilterExpressionParser()
    parser._Reset()

    next_state = parser._AddBracketOpen()
    self.assertIsNone(next_state)
    self.assertEqual(parser._stack[0], '(')

  # TODO: add tests for _CombineBinaryExpressions

  def testCombineParenthesis(self):
    """Tests the _CombineParenthesis function."""
    parser = expression_parser.EventFilterExpressionParser()
    parser._Reset()

    parser._CombineParenthesis()

    parser._AddBracketOpen()
    parser._AddBinaryOperator(string='&&')
    parser._AddBracketClose()
    self.assertEqual(len(parser._stack), 3)

    parser._CombineParenthesis()
    self.assertEqual(len(parser._stack), 1)

  def testGetNextToken(self):
    """Tests the _GetNextToken function."""
    parser = expression_parser.EventFilterExpressionParser()
    parser._Reset()

    parser._buffer = ''
    token = parser._GetNextToken()
    self.assertIsNone(token)

    parser._buffer = '('
    token = parser._GetNextToken()
    self.assertIsNotNone(token)
    self.assertEqual(parser._buffer, '')
    self.assertEqual(parser._processed_buffer, '(')

  # TODO: add tests for _NegateExpression

  def testPopState(self):
    """Tests the _PopState function."""
    parser = expression_parser.EventFilterExpressionParser()
    parser._Reset()

    parser._state_stack.append('INITIAL')
    self.assertEqual(len(parser._state_stack), 1)

    next_state = parser._PopState()
    self.assertEqual(next_state, 'INITIAL')
    self.assertEqual(len(parser._state_stack), 0)

    with self.assertRaises(errors.ParseError):
      parser._PopState()

  def testPushBack(self):
    """Tests the _PushBack function."""
    parser = expression_parser.EventFilterExpressionParser()
    parser._Reset()

    parser._buffer = ''
    parser._processed_buffer = 'mytest'

    next_state = parser._PushBack(string='test')
    self.assertIsNone(next_state)
    self.assertEqual(parser._buffer, 'test')
    self.assertEqual(parser._processed_buffer, 'my')

  def testPushState(self):
    """Tests the _PushState function."""
    parser = expression_parser.EventFilterExpressionParser()
    parser._Reset()

    parser._state = 'INITIAL'
    self.assertEqual(len(parser._state_stack), 0)

    next_state = parser._PushState()
    self.assertIsNone(next_state)
    self.assertEqual(len(parser._state_stack), 1)
    self.assertEqual(parser._state_stack[0], 'INITIAL')
    self.assertEqual(parser._state, 'INITIAL')

  # TODO: add tests for _Reduce

  def testReset(self):
    """Tests the _Reset function."""
    parser = expression_parser.EventFilterExpressionParser()
    parser._Reset()

  def testSetAttribute(self):
    """Tests the _SetAttribute function."""
    parser = expression_parser.EventFilterExpressionParser()
    parser._Reset()

    next_state = parser._SetAttribute(string='attribute')
    self.assertEqual(next_state, 'OPERATOR')

  def testSetOperator(self):
    """Tests the _SetOperator function."""
    parser = expression_parser.EventFilterExpressionParser()
    parser._Reset()

    self.assertIsNotNone(parser._current_expression)
    self.assertIsNone(parser._current_expression.operator)

    next_state = parser._SetOperator(string='&&')
    self.assertIsNone(next_state)
    self.assertEqual(parser._current_expression.operator, '&&')

  def testStringEscape(self):
    """Tests the _StringEscape function."""
    parser = expression_parser.EventFilterExpressionParser()
    parser._Reset()

    parser._StringStart()
    self.assertEqual(parser._string, '')

    match = re.compile(r'\\(.)').match('\\n')
    next_state = parser._StringEscape(string='\\n', match=match)
    self.assertIsNone(next_state)
    self.assertEqual(parser._string, '\n')

    with self.assertRaises(errors.ParseError):
      match = re.compile(r'\\(.)').match('\\q')
      parser._StringEscape(string='\\q', match=match)

  def testStringFinish(self):
    """Tests the _StringFinish function."""
    parser = expression_parser.EventFilterExpressionParser()
    parser._Reset()

    next_state = parser._StringFinish()
    self.assertIsNone(next_state)

  def testStringInsert(self):
    """Tests the _StringInsert function."""
    parser = expression_parser.EventFilterExpressionParser()
    parser._Reset()

    parser._StringStart()
    self.assertEqual(parser._string, '')

    next_state = parser._StringInsert(string='string')
    self.assertIsNone(next_state)
    self.assertEqual(parser._string, 'string')

  def testStringStart(self):
    """Tests the _StringStart function."""
    parser = expression_parser.EventFilterExpressionParser()
    parser._Reset()

    next_state = parser._StringStart()
    self.assertIsNone(next_state)
    self.assertEqual(parser._string, '')

  def testDefault(self):
    """Tests the Default function."""
    parser = expression_parser.EventFilterExpressionParser()

    parser.Default()

  # TODO: add tests for HexEscape
  # TODO: add tests for InsertArg
  # TODO: add tests for InsertFloatArg
  # TODO: add tests for InsertIntArg
  # TODO: add tests for InsertInt16Arg

  def testParse(self):
    """Tests the Parse function."""
    parser = expression_parser.EventFilterExpressionParser()

    # Arguments are either int, float or quoted string.
    expression = parser.Parse('attribute == 1')
    self.assertIsNotNone(expression)

    expression = parser.Parse('attribute == 0x10')
    self.assertIsNotNone(expression)

    with self.assertRaises(errors.ParseError):
      parser.Parse('attribute == 1a')

    expression = parser.Parse('attribute == 1.2')
    self.assertIsNotNone(expression)

    expression = parser.Parse('attribute == \'bla\'')
    self.assertIsNotNone(expression)

    expression = parser.Parse('attribute == "bla"')
    self.assertIsNotNone(expression)

    with self.assertRaises(errors.ParseError):
      parser.Parse('something == red')

    # Can't start with AND.
    with self.assertRaises(errors.ParseError):
      parser.Parse('and something is \'Blue\'')

    # Test negative filters.
    with self.assertRaises(errors.ParseError):
      parser.Parse('attribute not == \'dancer\'')

    with self.assertRaises(errors.ParseError):
      parser.Parse('attribute == not \'dancer\'')

    with self.assertRaises(errors.ParseError):
      parser.Parse('attribute not not equals \'dancer\'')

    with self.assertRaises(errors.ParseError):
      parser.Parse('attribute not > 23')

  def testParseWithBraces(self):
    """Tests the Parse function with braces."""
    parser = expression_parser.EventFilterExpressionParser()

    expression = parser.Parse('(a is 3)')
    self.assertIsNotNone(expression)

    # Need to close braces.
    with self.assertRaises(errors.ParseError):
      parser.Parse('(a is 3')

    # Need to open braces to close them.
    with self.assertRaises(errors.ParseError):
      parser.Parse('a is 3)')

  def testParseWithEscaping(self):
    """Tests the Parse function with escaping."""
    parser = expression_parser.EventFilterExpressionParser()

    expression = parser.Parse(r'a is "\n"')
    self.assertEqual(expression.args[0], '\n')

    # Can escape the backslash.
    expression = parser.Parse(r'a is "\\"')
    self.assertEqual(expression.args[0], '\\')

    # Invalid escape sequence.
    with self.assertRaises(errors.ParseError):
      parser.Parse(r'a is "\z"')

  def testParseWithHexadecimalEscaping(self):
    """Tests the Parse function with hexadecimal escaping."""
    parser = expression_parser.EventFilterExpressionParser()

    # Instead, this is what one should write.
    expression = parser.Parse(r'a is "\\xJZ"')
    self.assertEqual(expression.args[0], r'\xJZ')

    # Standard hex-escape.
    expression = parser.Parse('a is "\x41\x41\x41"')
    self.assertEqual(expression.args[0], 'AAA')

    # Hex-escape + a character.
    expression = parser.Parse('a is "\x414"')
    self.assertEqual(expression.args[0], 'A4')

    # How to include r'\x41'.
    expression = parser.Parse('a is "\\x41"')
    self.assertEqual(expression.args[0], '\x41')

    # This fails as it's not really a hex escaped string.
    with self.assertRaises(errors.ParseError):
      parser.Parse(r'a is "\xJZ"')

  def testParseWithEvents(self):
    """Tests the Parse function with events."""
    event = events.EventObject()
    event.timestamp = timelib.Timestamp.CopyFromString(
        '2015-11-18 01:15:43')
    event.timestamp_desc = 'Last Written'

    # TODO: refactor to event data
    event.data_type = 'Weirdo:Made up Source:Last Written'
    event.display_name = (
        'unknown:/My Documents/goodfella/Documents/Hideout/myfile.txt')
    event.filename = '/My Documents/goodfella/Documents/Hideout/myfile.txt'
    event.hostname = 'Agrabah'
    event.inode = 1245
    event.mydict = {
        'value': 134, 'another': 'value', 'A Key (with stuff)': 'Here'}
    event.parser = 'Weirdo'
    event.text = (
        'User did a very bad thing, bad, bad thing that awoke Dr. Evil.')
    event.text_short = (
        'This description is different than the long one.')

    event.tag = events.EventTag(comment='comment')
    event.tag.AddLabel('browser_search')

    # Series of tests.
    query = 'filename contains \'GoodFella\''
    self._CheckFilterEvent(event, query, True)

    # Double negative matching -> should be the same
    # as a positive one.
    parser = expression_parser.EventFilterExpressionParser()

    query = 'filename not not contains \'GoodFella\''
    with self.assertRaises(errors.ParseError):
      parser.Parse(query)

    # Test date filtering.
    query = 'date >= \'2015-11-18\''
    self._CheckFilterEvent(event, query, True)

    query = 'date < \'2015-11-19\''
    self._CheckFilterEvent(event, query, True)

    # 2015-11-18T01:15:43
    query = (
        'date < \'2015-11-18T01:15:44.341\' and '
        'date > \'2015-11-18 01:15:42\'')
    self._CheckFilterEvent(event, query, True)

    query = 'date > \'2015-11-19\''
    self._CheckFilterEvent(event, query, False)

    # Perform few attribute tests.
    query = 'filename not contains \'sometext\''
    self._CheckFilterEvent(event, query, True)

    query = (
        'timestamp_desc CONTAINS \'written\' AND date > \'2015-11-18\' AND '
        'date < \'2015-11-25 12:56:21\' AND (source_short contains \'LOG\' or '
        'source_short CONTAINS \'REG\')')
    self._CheckFilterEvent(event, query, True)

    query = 'parser is not \'Made\''
    self._CheckFilterEvent(event, query, True)

    query = 'parser is not \'Weirdo\''
    self._CheckFilterEvent(event, query, False)

    query = 'mydict.value is 123'
    self._CheckFilterEvent(event, query, False)

    query = 'mydict.akeywithstuff contains "ere"'
    self._CheckFilterEvent(event, query, True)

    query = 'mydict.value is 134'
    self._CheckFilterEvent(event, query, True)

    query = 'mydict.value < 200'
    self._CheckFilterEvent(event, query, True)

    query = 'mydict.another contains "val"'
    self._CheckFilterEvent(event, query, True)

    query = 'mydict.notthere is 123'
    self._CheckFilterEvent(event, query, False)

    query = 'source_long not contains \'Fake\''
    self._CheckFilterEvent(event, query, False)

    query = 'source is \'REG\''
    self._CheckFilterEvent(event, query, True)

    query = 'source is not \'FILE\''
    self._CheckFilterEvent(event, query, True)

    query = 'tag contains \'browser_search\''
    self._CheckFilterEvent(event, query, True)

    # Multiple attributes.
    query = (
        'source_long is \'Fake Parsing Source\' AND description_long '
        'regexp \'bad, bad thing [\\sa-zA-Z\\.]+ evil\'')
    self._CheckFilterEvent(event, query, False)

    query = (
        'source_long is \'Fake Parsing Source\' AND text iregexp '
        '\'bad, bad thing [\\sa-zA-Z\\.]+ evil\'')
    self._CheckFilterEvent(event, query, True)


# pylint: disable=missing-docstring


class ObjectFilterTest(unittest.TestCase):

  _OPERATOR_TESTS = {
      filters.LessThanOperator: [
          (True, ['size', 1000]),
          (True, ['size', 11]),
          (False, ['size', 10]),
          (False, ['size', 0]),
          (False, ['float', 1.0]),
          (True, ['float', 123.9824])],
      filters.LessEqualOperator: [
          (True, ['size', 1000]),
          (True, ['size', 11]),
          (True, ['size', 10]),
          (False, ['size', 9]),
          (False, ['float', 1.0]),
          (True, ['float', 123.9823])],
      filters.GreaterThanOperator: [
          (True, ['size', 1]),
          (True, ['size', 9.23]),
          (False, ['size', 10]),
          (False, ['size', 1000]),
          (True, ['float', 122]),
          (True, ['float', 1.0])],
      filters.GreaterEqualOperator: [
          (False, ['size', 1000]),
          (False, ['size', 11]),
          (True, ['size', 10]),
          (True, ['size', 0]),
          # Floats work fine too.
          (True, ['float', 122]),
          (True, ['float', 123.9823]),
          # Comparisons works with strings, although it might be a bit silly.
          (True, ['name', 'aoot.ini'])],
      filters.Contains: [
          # Contains works with strings.
          (True, ['name', 'boot.ini']),
          (True, ['name', 'boot']),
          (False, ['name', 'meh']),
          # Works with generators.
          (True, ['imported_dlls.imported_functions', 'FindWindow']),
          # But not with numbers.
          (False, ['size', 12])],
      filters.EqualsOperator: [
          (True, ['name', 'boot.ini']),
          (False, ['name', 'foobar']),
          (True, ['float', 123.9823])],
      filters.NotEqualsOperator: [
          (False, ['name', 'boot.ini']),
          (True, ['name', 'foobar']),
          (True, ['float', 25])],
      filters.InSet: [
          (True, ['name', ['boot.ini', 'autoexec.bat']]),
          (True, ['name', 'boot.ini']),
          (False, ['name', 'NOPE']),
          # All values of attributes are within these.
          (True, ['attributes', ['Archive', 'Backup', 'Nonexisting']]),
          # Not all values of attributes are within these.
          (False, ['attributes', ['Executable', 'Sparse']])],
      filters.Regexp: [
          (True, ['name', '^boot.ini$']),
          (True, ['name', 'boot.ini']),
          (False, ['name', '^$']),
          (True, ['attributes', 'Archive']),
          # One can regexp numbers if he's inclined to.
          (True, ['size', 0]),
          # But regexp doesn't work with lists or generators for the moment.
          (False, ['imported_dlls.imported_functions', 'FindWindow'])],
      }

  def setUp(self):
    """Makes preparations before running an individual test."""
    self.file = test_lib.DummyFile()

  def testBinaryOperators(self):
    for operator, test_data in self._OPERATOR_TESTS.items():
      for test_unit in test_data:
        ops = operator(arguments=test_unit[1])
        self.assertEqual(
            test_unit[0], ops.Matches(self.file),
            'test case {0!s} failed'.format(test_unit))
        if hasattr(ops, 'FlipBool'):
          ops.FlipBool()
          self.assertEqual(not test_unit[0], ops.Matches(self.file))

  def testGenericBinaryOperator(self):
    class TestBinaryOperator(filters.GenericBinaryOperator):
      values = list()

      def Operation(self, x, _):
        return self.values.append(x)

    # Test a common binary operator.
    tbo = TestBinaryOperator(arguments=['whatever', 0])
    self.assertEqual(tbo.right_operand, 0)
    self.assertEqual(tbo.args[0], 'whatever')
    tbo.Matches(test_lib.DummyObject('whatever', 'id'))
    tbo.Matches(test_lib.DummyObject('whatever', 'id2'))
    tbo.Matches(test_lib.DummyObject('whatever', 'bg'))
    tbo.Matches(test_lib.DummyObject('whatever', 'bg2'))
    self.assertListEqual(tbo.values, ['id', 'id2', 'bg', 'bg2'])

  def testRegexpRaises(self):
    with self.assertRaises(ValueError):
      filters.Regexp(arguments=['name', 'I [dont compile'])

  def testCompile(self):
    obj = test_lib.DummyObject('something', 'Blue')
    parser = expression_parser.EventFilterExpressionParser()
    expression = parser.Parse('something == \'Blue\'')
    event_filter = expression.Compile()
    self.assertEqual(event_filter.Matches(obj), True)

    expression = parser.Parse('something == \'Red\'')
    event_filter = expression.Compile()
    self.assertEqual(event_filter.Matches(obj), False)

    expression = parser.Parse('something == "Red"')
    event_filter = expression.Compile()
    self.assertEqual(event_filter.Matches(obj), False)

    obj = test_lib.DummyObject('size', 4)
    expression = parser.Parse('size < 3')
    event_filter = expression.Compile()
    self.assertEqual(event_filter.Matches(obj), False)

    expression = parser.Parse('size == 4')
    event_filter = expression.Compile()
    self.assertEqual(event_filter.Matches(obj), True)

    expression = parser.Parse('something is \'Blue\' and size not contains 3')
    event_filter = expression.Compile()
    self.assertEqual(event_filter.Matches(obj), False)


if __name__ == "__main__":
  unittest.main()
