#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""Tests for the event filter functions."""

from __future__ import unicode_literals

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

  # TODO: add tests for _AddBinaryOperator
  # TODO: add tests for _CombineBinaryExpressions
  # TODO: add tests for _CombineParenthesis
  # TODO: add tests for _GetNextToken
  # TODO: add tests for _NegateExpression
  # TODO: add tests for _PushBack
  # TODO: add tests for _Reduce
  # TODO: add tests for _Reset

  def testBracketClose(self):
    """Tests the BracketClose function."""
    parser = expression_parser.EventFilterExpressionParser()

    parser.BracketClose()

  def testBracketOpen(self):
    """Tests the BracketOpen function."""
    parser = expression_parser.EventFilterExpressionParser()

    parser.BracketOpen()

  def testDefault(self):
    """Tests the Default function."""
    parser = expression_parser.EventFilterExpressionParser()

    parser.Default()

  # TODO: add tests for InsertArg
  # TODO: add tests for Parse
  # TODO: add tests for PopState
  # TODO: add tests for PushState
  # TODO: add tests for StringEscape

  def testStringFinish(self):
    """Tests the StringFinish function."""
    parser = expression_parser.EventFilterExpressionParser()

    state = parser.StringFinish()
    self.assertIsNone(state)

  def testStringInsert(self):
    """Tests the StringInsert function."""
    parser = expression_parser.EventFilterExpressionParser()

    parser.StringStart()
    parser.StringInsert(string='string')

  def testStringStart(self):
    """Tests the StringStart function."""
    parser = expression_parser.EventFilterExpressionParser()

    parser.StringStart()

  def testStoreAttribute(self):
    """Tests the StoreAttribute function."""
    parser = expression_parser.EventFilterExpressionParser()
    parser._Reset()

    token = parser.StoreAttribute(string='attribute')
    self.assertEqual(token, 'OPERATOR')

  def testStoreOperator(self):
    """Tests the StoreOperator function."""
    parser = expression_parser.EventFilterExpressionParser()
    parser._Reset()

    parser.StoreOperator(string='and')


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

  def testContext(self):
    with self.assertRaises(errors.InvalidNumberOfOperands):
      filters.ContextOperator(arguments=['context'])

    with self.assertRaises(errors.InvalidNumberOfOperands):
      filters.ContextOperator(arguments=[
          'context', filters.EqualsOperator(arguments=['path', 'value']),
          filters.EqualsOperator(arguments=['another_path', 'value'])])

    # One imported_dll imports 2 functions AND one imported_dll imports
    # function RegQueryValueEx.
    arguments = [
        filters.EqualsOperator(arguments=[
            'imported_dlls.num_imported_functions', 1]),
        filters.Contains(arguments=[
            'imported_dlls.imported_functions', 'RegQueryValueEx'])]
    condition = filters.AndFilter(arguments=arguments)

    # Without context, it matches because both filters match separately.
    self.assertEqual(True, condition.Matches(self.file))

    arguments = [
        filters.EqualsOperator(arguments=['num_imported_functions', 2]),
        filters.Contains(arguments=['imported_functions', 'RegQueryValueEx'])]
    condition = filters.AndFilter(arguments=arguments)

    # The same DLL imports 2 functions AND one of these is RegQueryValueEx.
    context = filters.ContextOperator(arguments=['imported_dlls', condition])

    # With context, it doesn't match because both don't match in the same dll.
    self.assertEqual(False, context.Matches(self.file))

    # One imported_dll imports only 1 function AND one imported_dll imports
    # function RegQueryValueEx.
    condition = filters.AndFilter(arguments=[
        filters.EqualsOperator(arguments=['num_imported_functions', 1]),
        filters.Contains(arguments=['imported_functions', 'RegQueryValueEx'])])

    # The same DLL imports 1 function AND it's RegQueryValueEx.
    context = filters.ContextOperator(['imported_dlls', condition])
    self.assertEqual(True, context.Matches(self.file))

    # Now test the context with a straight query.
    query = '\n'.join([
        '@imported_dlls',
        '(',
        '  imported_functions contains "RegQueryValueEx"',
        '  AND num_imported_functions == 1',
        ')'])

    parser = expression_parser.EventFilterExpressionParser()
    expression = parser.Parse(query)
    event_filter = expression.Compile()
    self.assertEqual(True, event_filter.Matches(self.file))

  def testRegexpRaises(self):
    with self.assertRaises(ValueError):
      filters.Regexp(arguments=['name', 'I [dont compile'])

  def testEscaping(self):
    parser = expression_parser.EventFilterExpressionParser()
    expression = parser.Parse(r'a is "\n"')
    self.assertEqual(expression.args[0], '\n')

    # Invalid escape sequence.
    parser = expression_parser.EventFilterExpressionParser()
    with self.assertRaises(errors.ParseError):
      parser.Parse(r'a is "\z"')

    # Can escape the backslash.
    parser = expression_parser.EventFilterExpressionParser()
    expression = parser.Parse(r'a is "\\"')
    self.assertEqual(expression.args[0], '\\')

    # Test hexadecimal escaping.

    # This fails as it's not really a hex escaped string.
    parser = expression_parser.EventFilterExpressionParser()
    with self.assertRaises(errors.ParseError):
      parser.Parse(r'a is "\xJZ"')

    # Instead, this is what one should write.
    parser = expression_parser.EventFilterExpressionParser()
    expression = parser.Parse(r'a is "\\xJZ"')
    self.assertEqual(expression.args[0], r'\xJZ')

    # Standard hex-escape.
    parser = expression_parser.EventFilterExpressionParser()
    expression = parser.Parse('a is "\x41\x41\x41"')
    self.assertEqual(expression.args[0], 'AAA')

    # Hex-escape + a character.
    parser = expression_parser.EventFilterExpressionParser()
    expression = parser.Parse('a is "\x414"')
    self.assertEqual(expression.args[0], 'A4')

    # How to include r'\x41'.
    parser = expression_parser.EventFilterExpressionParser()
    expression = parser.Parse('a is "\\x41"')
    self.assertEqual(expression.args[0], '\x41')

  def testParse(self):
    # Arguments are either int, float or quoted string.
    parser = expression_parser.EventFilterExpressionParser()
    expression = parser.Parse('attribute == 1')
    self.assertIsNotNone(expression)

    parser = expression_parser.EventFilterExpressionParser()
    expression = parser.Parse('attribute == 0x10')
    self.assertIsNotNone(expression)

    parser = expression_parser.EventFilterExpressionParser()
    with self.assertRaises(errors.ParseError):
      parser.Parse('attribute == 1a')

    parser = expression_parser.EventFilterExpressionParser()
    expression = parser.Parse('attribute == 1.2')
    self.assertIsNotNone(expression)

    parser = expression_parser.EventFilterExpressionParser()
    expression = parser.Parse('attribute == \'bla\'')
    self.assertIsNotNone(expression)

    parser = expression_parser.EventFilterExpressionParser()
    expression = parser.Parse('attribute == "bla"')
    self.assertIsNotNone(expression)

    parser = expression_parser.EventFilterExpressionParser()
    with self.assertRaises(errors.ParseError):
      parser.Parse('something == red')

    # Can't start with AND.
    parser = expression_parser.EventFilterExpressionParser()
    with self.assertRaises(errors.ParseError):
      parser.Parse('and something is \'Blue\'')

    # Test negative filters.
    parser = expression_parser.EventFilterExpressionParser()
    with self.assertRaises(errors.ParseError):
      parser.Parse('attribute not == \'dancer\'')

    parser = expression_parser.EventFilterExpressionParser()
    with self.assertRaises(errors.ParseError):
      parser.Parse('attribute == not \'dancer\'')

    parser = expression_parser.EventFilterExpressionParser()
    with self.assertRaises(errors.ParseError):
      parser.Parse('attribute not not equals \'dancer\'')

    parser = expression_parser.EventFilterExpressionParser()
    with self.assertRaises(errors.ParseError):
      parser.Parse('attribute not > 23')

    # Need to close braces.
    parser = expression_parser.EventFilterExpressionParser()
    expression = parser.Parse('(a is 3)')
    self.assertIsNotNone(expression)

    parser = expression_parser.EventFilterExpressionParser()
    with self.assertRaises(errors.ParseError):
      parser.Parse('(a is 3')

    # Need to open braces to close them.
    parser = expression_parser.EventFilterExpressionParser()
    with self.assertRaises(errors.ParseError):
      parser.Parse('a is 3)')

    # Context Operator alone is not accepted.
    parser = expression_parser.EventFilterExpressionParser()
    with self.assertRaises(errors.ParseError):
      parser.Parse('@attributes')

    # Accepted only with braces.
    parser = expression_parser.EventFilterExpressionParser()
    expression = parser.Parse('@attributes( name is \'adrien\')')
    self.assertIsNotNone(expression)

    # Not without them.
    parser = expression_parser.EventFilterExpressionParser()
    with self.assertRaises(errors.ParseError):
      parser.Parse('@attributes name is \'adrien\'')

    # Can nest context operators.
    parser = expression_parser.EventFilterExpressionParser()
    expression = parser.Parse(
        '@imported_dlls( @imported_function( name is \'OpenFileA\'))')
    self.assertIsNotNone(expression)

    # Can nest context operators and mix braces without it messing up.
    parser = expression_parser.EventFilterExpressionParser()
    expression = parser.Parse(
        '@imported_dlls( @imported_function( name is \'OpenFileA\'))')
    self.assertIsNotNone(expression)

    query = '\n'.join([
        '@imported_dlls',
        '(',
        '  @imported_function',
        '  (',
        '    name is "OpenFileA" and ordinal == 12',
        '  )',
        ')'])

    parser = expression_parser.EventFilterExpressionParser()
    expression = parser.Parse(query)
    self.assertIsNotNone(expression)

    # Mix context and binary operators.
    query = '\n'.join([
        '@imported_dlls',
        '(',
        '  @imported_function',
        '  (',
        '    name is "OpenFileA"',
        '  ) AND num_functions == 2',
        ')'])

    parser = expression_parser.EventFilterExpressionParser()
    expression = parser.Parse(query)
    self.assertIsNotNone(expression)

    # Also on the right.
    query = '\n'.join([
        '@imported_dlls',
        '(',
        '  num_functions == 2 AND',
        '  @imported_function',
        '  (',
        '    name is "OpenFileA"',
        '  )',
        ')'])

    parser = expression_parser.EventFilterExpressionParser()
    with self.assertRaises(errors.ParseError):
      parser.Parse(query)

    # Altogether.
    # There's an imported dll that imports OpenFileA AND
    # an imported DLL matching advapi32.dll that imports RegQueryValueExA AND
    # and it exports a symbol called 'inject'.
    query = '\n'.join([
        '@imported_dlls( @imported_function ( name is "OpenFileA" ) )',
        'AND',
        '@imported_dlls (',
        '  name regexp "(?i)advapi32.dll"',
        '  AND @imported_function ( name is "RegQueryValueEx" )',
        ')',
        'AND @exported_symbols(name is "inject")'])

    parser = expression_parser.EventFilterExpressionParser()
    with self.assertRaises(errors.ParseError):
      parser.Parse(query)

  def testCompile(self):
    obj = test_lib.DummyObject('something', 'Blue')
    parser = expression_parser.EventFilterExpressionParser()
    expression = parser.Parse('something == \'Blue\'')
    event_filter = expression.Compile()
    self.assertEqual(event_filter.Matches(obj), True)

    parser = expression_parser.EventFilterExpressionParser()
    expression = parser.Parse('something == \'Red\'')
    event_filter = expression.Compile()
    self.assertEqual(event_filter.Matches(obj), False)

    parser = expression_parser.EventFilterExpressionParser()
    expression = parser.Parse('something == "Red"')
    event_filter = expression.Compile()
    self.assertEqual(event_filter.Matches(obj), False)

    obj = test_lib.DummyObject('size', 4)
    parser = expression_parser.EventFilterExpressionParser()
    expression = parser.Parse('size < 3')
    event_filter = expression.Compile()
    self.assertEqual(event_filter.Matches(obj), False)

    parser = expression_parser.EventFilterExpressionParser()
    expression = parser.Parse('size == 4')
    event_filter = expression.Compile()
    self.assertEqual(event_filter.Matches(obj), True)

    parser = expression_parser.EventFilterExpressionParser()
    expression = parser.Parse('something is \'Blue\' and size not contains 3')
    event_filter = expression.Compile()
    self.assertEqual(event_filter.Matches(obj), False)


class PFilterTest(unittest.TestCase):
  """Simple plaso specific tests to the expression parser implementation."""

  def _RunPlasoTest(self, event, query, expected_result):
    """Run a simple test against an event object.

    Args:
      event (EventObject): event.
      query (str): event filter expression.
      expected_result (bool): expected result.
    """
    parser = expression_parser.EventFilterExpressionParser()
    expression = parser.Parse(query)
    event_filter = expression.Compile()

    self.assertEqual(
        expected_result, event_filter.Matches(event),
        'query {0:s} failed with event {1!s}'.format(query, event.CopyToDict()))

  def testPlasoEvents(self):
    """Test plaso EventObjects, both Python and Protobuf version.

    These are more plaso specific tests than the more generic object filter
    ones. It will create an event object that stores some attributes. These
    objects will then be serialized and all tests run against both the Python
    objects as well as the serialized ones.
    """
    event = events.EventObject()
    event.data_type = 'Weirdo:Made up Source:Last Written'
    event.timestamp = timelib.Timestamp.CopyFromString(
        '2015-11-18 01:15:43')
    event.timestamp_desc = 'Last Written'
    event.text_short = (
        'This description is different than the long one.')
    event.text = (
        'User did a very bad thing, bad, bad thing that awoke Dr. Evil.')
    event.filename = (
        '/My Documents/goodfella/Documents/Hideout/myfile.txt')
    event.hostname = 'Agrabah'
    event.parser = 'Weirdo'
    event.inode = 1245
    event.mydict = {
        'value': 134, 'another': 'value', 'A Key (with stuff)': 'Here'}
    event.display_name = 'unknown:{0:s}'.format(event.filename)

    event.tag = events.EventTag(comment='comment')
    event.tag.AddLabel('browser_search')

    # Series of tests.
    query = 'filename contains \'GoodFella\''
    self._RunPlasoTest(event, query, True)

    # Double negative matching -> should be the same
    # as a positive one.
    query = 'filename not not contains \'GoodFella\''
    parser = expression_parser.EventFilterExpressionParser()
    with self.assertRaises(errors.ParseError):
      parser.Parse(query)

    # Test date filtering.
    query = 'date >= \'2015-11-18\''
    self._RunPlasoTest(event, query, True)

    query = 'date < \'2015-11-19\''
    self._RunPlasoTest(event, query, True)

    # 2015-11-18T01:15:43
    query = (
        'date < \'2015-11-18T01:15:44.341\' and '
        'date > \'2015-11-18 01:15:42\'')
    self._RunPlasoTest(event, query, True)

    query = 'date > \'2015-11-19\''
    self._RunPlasoTest(event, query, False)

    # Perform few attribute tests.
    query = 'filename not contains \'sometext\''
    self._RunPlasoTest(event, query, True)

    query = (
        'timestamp_desc CONTAINS \'written\' AND date > \'2015-11-18\' AND '
        'date < \'2015-11-25 12:56:21\' AND (source_short contains \'LOG\' or '
        'source_short CONTAINS \'REG\')')
    self._RunPlasoTest(event, query, True)

    query = 'parser is not \'Made\''
    self._RunPlasoTest(event, query, True)

    query = 'parser is not \'Weirdo\''
    self._RunPlasoTest(event, query, False)

    query = 'mydict.value is 123'
    self._RunPlasoTest(event, query, False)

    query = 'mydict.akeywithstuff contains "ere"'
    self._RunPlasoTest(event, query, True)

    query = 'mydict.value is 134'
    self._RunPlasoTest(event, query, True)

    query = 'mydict.value < 200'
    self._RunPlasoTest(event, query, True)

    query = 'mydict.another contains "val"'
    self._RunPlasoTest(event, query, True)

    query = 'mydict.notthere is 123'
    self._RunPlasoTest(event, query, False)

    query = 'source_long not contains \'Fake\''
    self._RunPlasoTest(event, query, False)

    query = 'source is \'REG\''
    self._RunPlasoTest(event, query, True)

    query = 'source is not \'FILE\''
    self._RunPlasoTest(event, query, True)

    query = 'tag contains \'browser_search\''
    self._RunPlasoTest(event, query, True)

    # Multiple attributes.
    query = (
        'source_long is \'Fake Parsing Source\' AND description_long '
        'regexp \'bad, bad thing [\\sa-zA-Z\\.]+ evil\'')
    self._RunPlasoTest(event, query, False)

    query = (
        'source_long is \'Fake Parsing Source\' AND text iregexp '
        '\'bad, bad thing [\\sa-zA-Z\\.]+ evil\'')
    self._RunPlasoTest(event, query, True)


if __name__ == "__main__":
  unittest.main()
