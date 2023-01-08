#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""Tests for the event filter functions."""

import re
import unittest

from plaso.containers import events
from plaso.filters import expression_parser
from plaso.filters import filters
from plaso.lib import errors

from tests import test_lib as shared_test_lib
from tests.containers import test_lib as containers_test_lib


class TestBinaryOperator(filters.GenericBinaryOperator):
  """Binary operator for testing.

  Attributes:
    values (list[str]): event values passed to the _CompareValue function.
  """

  def __init__(self, arguments=None, **kwargs):
    """Initializes a binary operator.

    Args:
      arguments (Optional[object]): operands of the filter.
    """
    super(TestBinaryOperator, self).__init__(arguments=arguments, **kwargs)
    self.values = []

  def _CompareValue(self, event_value, filter_value):
    """Compares if two values are not equal.

    Args:
      event_value (object): value retrieved from the event.
      filter_value (object): value defined by the filter.

    Returns:
      bool: True if the values are not equal, False otherwise.
    """
    self.values.append(event_value)
    return True


class TokenTest(shared_test_lib.BaseTestCase):
  """Tests the event filter parser token."""

  def testInitialize(self):
    """Tests the __init__ function."""
    token = expression_parser.Token('STRING', r'\\(.)', 'StringEscape', None)
    self.assertIsNotNone(token)


class EventFilterExpressionParserTest(shared_test_lib.BaseTestCase):
  """Tests the event filter expression parser."""

  # pylint: disable=protected-access

  _TEST_EVENTS = [
      {'_parser_chain': 'test_parser',
       'data_type': 'test_log:entry',
       'display_name': (
           'unknown:/My Documents/goodfella/Documents/Hideout/myfile.txt'),
       'filename': '/My Documents/goodfella/Documents/Hideout/myfile.txt',
       'hostname': 'Agrabah',
       'inode': 1245,
       'text': 'User did a very bad thing, bad, bad thing that awoke Dr. Evil.',
       'text_short': 'This description is different than the long one.',
       'timestamp': '2015-11-18 01:15:43',
       'timestamp_desc': 'Last Written'}]

  def _CheckIfExpressionMatches(
      self, expression, event, event_data, event_data_stream, event_tag,
      expected_result):
    """Checks if the event filter expression matches the event values.

    Args:
      expression (str): event filter expression.
      event (EventObject): event.
      event_data (EventData): event data.
      event_data_stream (EventDataStream): event data stream.
      event_tag (EventTag): event tag.
      expected_result (bool): expected result.
    """
    parser = expression_parser.EventFilterExpressionParser()
    expression = parser.Parse(expression)
    event_filter = expression.Compile()

    result = event_filter.Matches(
        event, event_data, event_data_stream, event_tag)
    self.assertEqual(expected_result, result)

  # TODO: add tests for _AddArgument
  # TODO: add tests for _AddArgumentDateTime
  # TODO: add tests for _AddArgumentDecimalInteger
  # TODO: add tests for _AddArgumentFloatingPoint
  # TODO: add tests for _AddArgumentHexadecimalInteger

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

  def testNoOperation(self):
    """Tests the _NoOperation function."""
    parser = expression_parser.EventFilterExpressionParser()

    parser._NoOperation()

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

  def testStringExpand(self):
    """Tests the _StringExpand function."""
    parser = expression_parser.EventFilterExpressionParser()
    parser._Reset()

    parser._StringStart()
    self.assertEqual(parser._string, '')

    next_state = parser._StringExpand(string='string')
    self.assertIsNone(next_state)
    self.assertEqual(parser._string, 'string')

  def testStringFinish(self):
    """Tests the _StringFinish function."""
    parser = expression_parser.EventFilterExpressionParser()
    parser._Reset()

    next_state = parser._StringFinish()
    self.assertIsNone(next_state)

  def testStringStart(self):
    """Tests the _StringStart function."""
    parser = expression_parser.EventFilterExpressionParser()
    parser._Reset()

    next_state = parser._StringStart()
    self.assertIsNone(next_state)
    self.assertEqual(parser._string, '')

  # TODO: add tests for HexEscape

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

    # Test expression starting with AND.
    with self.assertRaises(errors.ParseError):
      parser.Parse('and something is \'Blue\'')

    # Test incorrect usage of NOT.
    with self.assertRaises(errors.ParseError):
      parser.Parse('attribute not == \'dancer\'')

    with self.assertRaises(errors.ParseError):
      parser.Parse('attribute == not \'dancer\'')

    with self.assertRaises(errors.ParseError):
      parser.Parse('attribute not not equals \'dancer\'')

    with self.assertRaises(errors.ParseError):
      parser.Parse('attribute not > 23')

    # Test double negative matching.
    with self.assertRaises(errors.ParseError):
      parser.Parse('filename not not contains \'GoodFella\'')

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
    event, event_data, _ = containers_test_lib.CreateEventFromValues(
        self._TEST_EVENTS[0])

    event_tag = events.EventTag()
    event_tag.AddLabel('browser_search')

    self._CheckIfExpressionMatches(
        'filename contains \'GoodFella\'', event, event_data, None, event_tag,
        True)

    # Test timestamp filtering.
    self._CheckIfExpressionMatches(
        'timestamp >= \'2015-11-18\'', event, event_data, None, event_tag, True)

    self._CheckIfExpressionMatches(
        'timestamp < \'2015-11-19\'', event, event_data, None, event_tag, True)

    expression = (
        'timestamp < \'2015-11-18T01:15:44.341\' and '
        'timestamp > \'2015-11-18 01:15:42\'')

    self._CheckIfExpressionMatches(
        expression, event, event_data, None, event_tag, True)

    self._CheckIfExpressionMatches(
        'timestamp > \'2015-11-19\'', event, event_data, None, event_tag, False)

    # Perform few attribute tests.
    self._CheckIfExpressionMatches(
        'filename not contains \'sometext\'', event, event_data, None,
        event_tag, True)

    expression = (
        'timestamp_desc CONTAINS \'written\' AND timestamp > \'2015-11-18\' '
        'AND timestamp < \'2015-11-25 12:56:21\'')

    self._CheckIfExpressionMatches(
        expression, event, event_data, None, event_tag, True)

    self._CheckIfExpressionMatches(
        'parser is not \'Made\'', event, event_data, None, event_tag, True)

    self._CheckIfExpressionMatches(
        'parser is not \'test_parser\'', event, event_data, None, event_tag,
        False)

    self._CheckIfExpressionMatches(
        'tag contains \'browser_search\'', event, event_data, None, event_tag,
        True)

    # Test multiple attributes.
    self._CheckIfExpressionMatches(
        'text iregexp \'bad, bad thing [a-zA-Z\\\\s.]+ evil\'', event,
        event_data, None, event_tag, True)


if __name__ == "__main__":
  unittest.main()
