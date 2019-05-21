#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""Tests for the event filter functions."""

from __future__ import unicode_literals

import unittest

from plaso.containers import events
from plaso.filters import expression_parser
from plaso.formatters import interface as formatters_interface
from plaso.formatters import manager as formatters_manager
from plaso.lib import errors
from plaso.lib import timelib

from tests import test_lib as shared_test_lib


class PfilterFakeFormatter(formatters_interface.EventFormatter):
  """A formatter for this fake class."""
  DATA_TYPE = 'Weirdo:Made up Source:Last Written'

  FORMAT_STRING = '{text}'
  FORMAT_STRING_SHORT = '{text_short}'

  SOURCE_LONG = 'Fake Parsing Source'
  SOURCE_SHORT = 'REG'


formatters_manager.FormattersManager.RegisterFormatter(PfilterFakeFormatter)


class TestFilterImplementation(expression_parser.BaseFilterImplementation):
  """Filter implementation for testing."""

  AndFilter = expression_parser.AndFilter
  IdentityFilter = expression_parser.IdentityFilter


class TokenTest(shared_test_lib.BaseTestCase):
  """Tests the event filter parser token."""

  def testInitialize(self):
    """Tests the __init__ function."""
    token = expression_parser.Token('STRING', r'\\(.)', 'StringEscape', None)
    self.assertIsNotNone(token)


class ExpressionTest(shared_test_lib.BaseTestCase):
  """Tests the event filter parser expression."""

  def testAddArg(self):
    """Tests the AddArg function."""
    expression = expression_parser.Expression()

    expression.AddArg('argument1')

    with self.assertRaises(errors.ParseError):
      expression.AddArg('argument2')

  def testSetAttribute(self):
    """Tests the SetAttribute function."""
    expression = expression_parser.Expression()

    expression.SetAttribute('attribute')

  def testSetOperator(self):
    """Tests the SetOperator function."""
    expression = expression_parser.Expression()

    expression.SetOperator('=')


class BinaryExpressionTest(shared_test_lib.BaseTestCase):
  """Tests the event filter parser binary expression."""

  def testAddOperands(self):
    """Tests the AddOperands function."""
    expression = expression_parser.BinaryExpression(operator='and')
    left_hand_expression = expression_parser.Expression()
    right_hand_expression = expression_parser.Expression()

    expression.AddOperands(left_hand_expression, right_hand_expression)

    with self.assertRaises(errors.ParseError):
      expression.AddOperands(None, right_hand_expression)

    with self.assertRaises(errors.ParseError):
      expression.AddOperands(left_hand_expression, None)

  def testCompile(self):
    """Tests the Compile function."""
    expression = expression_parser.BinaryExpression(operator='and')

    expression.Compile(TestFilterImplementation)

    expression = expression_parser.BinaryExpression()

    with self.assertRaises(errors.ParseError):
      expression.Compile(TestFilterImplementation)


class IdentityExpressionTest(shared_test_lib.BaseTestCase):
  """Tests the event filter parser identify expression."""

  def testCompile(self):
    """Tests the Compile function."""
    expression = expression_parser.IdentityExpression()
    expression.Compile(TestFilterImplementation)


class ParserTest(shared_test_lib.BaseTestCase):
  """Tests the expression_parser parser."""

  # TODO: add tests for _CombineBinaryExpressions
  # TODO: add tests for _CombineParenthesis
  # TODO: add tests for BinaryOperator

  def testBracketClose(self):
    """Tests the BracketClose function."""
    parser = expression_parser.EventFilterExpressionParser()

    parser.BracketClose()

  def testBracketOpen(self):
    """Tests the BracketOpen function."""
    parser = expression_parser.EventFilterExpressionParser()

    parser.BracketOpen()

  def testClose(self):
    """Tests the Close function."""
    parser = expression_parser.EventFilterExpressionParser()

    with self.assertRaises(errors.ParseError):
      parser.Close()

  def testDefault(self):
    """Tests the Default function."""
    parser = expression_parser.EventFilterExpressionParser()

    parser.Default()

  def testCompile(self):
    """Tests the Compile function."""
    parser = expression_parser.EventFilterExpressionParser()

    result = parser.Empty()
    self.assertTrue(result)

  # TODO: add tests for Error

  def testFeed(self):
    """Tests the Feed function."""
    parser = expression_parser.EventFilterExpressionParser()

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

    token = parser.StoreAttribute(string='attribute')
    self.assertEqual(token, 'OPERATOR')

  def testStoreOperator(self):
    """Tests the StoreOperator function."""
    parser = expression_parser.EventFilterExpressionParser()

    parser.StoreOperator(string='and')


# pylint: disable=missing-docstring


class DummyObject(object):
  def __init__(self, key, value):
    setattr(self, key, value)


class HashObject(object):
  def __init__(self, hash_value=None):
    self.value = hash_value

  @property
  def md5(self):
    return self.value

  def __eq__(self, y):
    return self.value == y

  def __lt__(self, y):
    return self.value < y


class Dll(object):
  def __init__(self, name, imported_functions=None, exported_functions=None):
    self.name = name
    self._imported_functions = imported_functions or []
    self.num_imported_functions = len(self._imported_functions)
    self.exported_functions = exported_functions or []
    self.num_exported_functions = len(self.exported_functions)

  @property
  def imported_functions(self):
    for fn in self._imported_functions:
      yield fn


class DummyFile(object):
  _FILENAME = 'boot.ini'

  ATTR1 = 'Backup'
  ATTR2 = 'Archive'
  HASH1 = '123abc'
  HASH2 = '456def'

  non_callable_leaf = 'yoda'

  def __init__(self):
    self.non_callable = HashObject(self.HASH1)
    self.non_callable_repeated = [
        DummyObject('desmond', ['brotha', 'brotha']),
        DummyObject('desmond', ['brotha', 'sista'])]
    self.imported_dll1 = Dll('a.dll', ['FindWindow', 'CreateFileA'])
    self.imported_dll2 = Dll('b.dll', ['RegQueryValueEx'])

  @property
  def name(self):
    return self._FILENAME

  @property
  def attributes(self):
    return [self.ATTR1, self.ATTR2]

  @property
  def hash(self):
    return [HashObject(self.HASH1), HashObject(self.HASH2)]

  @property
  def size(self):
    return 10

  @property
  def deferred_values(self):
    for v in ['a', 'b']:
      yield v

  @property
  def novalues(self):
    return []

  @property
  def imported_dlls(self):
    return [self.imported_dll1, self.imported_dll2]

  def Callable(self):
    raise RuntimeError('This can not be called.')

  @property
  def float(self):
    return 123.9823


class LowercaseAttributeFilterImplementation(
    expression_parser.BaseFilterImplementation):
  """Does field name access on the lowercase version of names.

  Useful to only access attributes and properties with Google's python naming
  style.
  """

  FILTERS = {}
  FILTERS.update(expression_parser.BaseFilterImplementation.FILTERS)
  FILTERS.update({
      'ValueExpander': expression_parser.LowercaseAttributeValueExpander})


class ObjectFilterTest(unittest.TestCase):

  def setUp(self):
    """Makes preparations before running an individual test."""
    self.file = DummyFile()
    self.value_expander = (
        LowercaseAttributeFilterImplementation.FILTERS['ValueExpander'])

  operator_tests = {
      expression_parser.Less: [
          (True, ['size', 1000]),
          (True, ['size', 11]),
          (False, ['size', 10]),
          (False, ['size', 0]),
          (False, ['float', 1.0]),
          (True, ['float', 123.9824])],
      expression_parser.LessEqual: [
          (True, ['size', 1000]),
          (True, ['size', 11]),
          (True, ['size', 10]),
          (False, ['size', 9]),
          (False, ['float', 1.0]),
          (True, ['float', 123.9823])],
      expression_parser.Greater: [
          (True, ['size', 1]),
          (True, ['size', 9.23]),
          (False, ['size', 10]),
          (False, ['size', 1000]),
          (True, ['float', 122]),
          (True, ['float', 1.0])],
      expression_parser.GreaterEqual: [
          (False, ['size', 1000]),
          (False, ['size', 11]),
          (True, ['size', 10]),
          (True, ['size', 0]),
          # Floats work fine too.
          (True, ['float', 122]),
          (True, ['float', 123.9823]),
          # Comparisons works with strings, although it might be a bit silly.
          (True, ['name', 'aoot.ini'])],
      expression_parser.Contains: [
          # Contains works with strings.
          (True, ['name', 'boot.ini']),
          (True, ['name', 'boot']),
          (False, ['name', 'meh']),
          # Works with generators.
          (True, ['imported_dlls.imported_functions', 'FindWindow']),
          # But not with numbers.
          (False, ['size', 12])],
      expression_parser.Equals: [
          (True, ['name', 'boot.ini']),
          (False, ['name', 'foobar']),
          (True, ['float', 123.9823])],
      expression_parser.NotEquals: [
          (False, ['name', 'boot.ini']),
          (True, ['name', 'foobar']),
          (True, ['float', 25])],
      expression_parser.InSet: [
          (True, ['name', ['boot.ini', 'autoexec.bat']]),
          (True, ['name', 'boot.ini']),
          (False, ['name', 'NOPE']),
          # All values of attributes are within these.
          (True, ['attributes', ['Archive', 'Backup', 'Nonexisting']]),
          # Not all values of attributes are within these.
          (False, ['attributes', ['Executable', 'Sparse']])],
      expression_parser.Regexp: [
          (True, ['name', '^boot.ini$']),
          (True, ['name', 'boot.ini']),
          (False, ['name', '^$']),
          (True, ['attributes', 'Archive']),
          # One can regexp numbers if he's inclined to.
          (True, ['size', 0]),
          # But regexp doesn't work with lists or generators for the moment.
          (False, ['imported_dlls.imported_functions', 'FindWindow'])],
      }

  def testBinaryOperators(self):
    for operator, test_data in self.operator_tests.items():
      for test_unit in test_data:
        kwargs = {'arguments': test_unit[1],
                  'value_expander': self.value_expander}
        ops = operator(**kwargs)
        self.assertEqual(
            test_unit[0], ops.Matches(self.file),
            'test case {0!s} failed'.format(test_unit))
        if hasattr(ops, 'FlipBool'):
          ops.FlipBool()
          self.assertEqual(not test_unit[0], ops.Matches(self.file))

  def testExpand(self):
    # Case insensitivity.
    values_lowercase = self.value_expander().Expand(self.file, 'size')
    values_uppercase = self.value_expander().Expand(self.file, 'Size')
    self.assertListEqual(list(values_lowercase), list(values_uppercase))

    # Existing, non-repeated, leaf is a value.
    values = self.value_expander().Expand(self.file, 'size')
    self.assertListEqual(list(values), [10])

    # Existing, non-repeated, leaf is iterable.
    values = self.value_expander().Expand(self.file, 'attributes')
    self.assertListEqual(list(values), [[DummyFile.ATTR1, DummyFile.ATTR2]])

    # Existing, repeated, leaf is value.
    values = self.value_expander().Expand(self.file, 'hash.md5')
    self.assertListEqual(list(values), [DummyFile.HASH1, DummyFile.HASH2])

    # Existing, repeated, leaf is iterable.
    values = self.value_expander().Expand(
        self.file, 'non_callable_repeated.desmond')
    self.assertListEqual(
        list(values), [['brotha', 'brotha'], ['brotha', 'sista']])

    # Now with an iterator.
    values = self.value_expander().Expand(self.file, 'deferred_values')
    self.assertListEqual([list(value) for value in values], [['a', 'b']])

    # Iterator > generator.
    values = self.value_expander().Expand(
        self.file, 'imported_dlls.imported_functions')
    expected = [['FindWindow', 'CreateFileA'], ['RegQueryValueEx']]
    self.assertListEqual([list(value) for value in values], expected)

    # Non-existing first path.
    values = self.value_expander().Expand(self.file, 'nonexistant')
    self.assertListEqual(list(values), [])

    # Non-existing in the middle.
    values = self.value_expander().Expand(self.file, 'hash.mink.boo')
    self.assertListEqual(list(values), [])

    # Non-existing as a leaf.
    values = self.value_expander().Expand(self.file, 'hash.mink')
    self.assertListEqual(list(values), [])

    # Non-callable leaf.
    values = self.value_expander().Expand(self.file, 'non_callable_leaf')
    self.assertListEqual(list(values), [DummyFile.non_callable_leaf])

    # callable.
    values = self.value_expander().Expand(self.file, 'Callable')
    self.assertListEqual(list(values), [])

    # leaf under a callable. Will return nothing.
    values = self.value_expander().Expand(self.file, 'Callable.a')
    self.assertListEqual(list(values), [])

  def testGenericBinaryOperator(self):
    class TestBinaryOperator(expression_parser.GenericBinaryOperator):
      values = list()

      def Operation(self, x, _):
        return self.values.append(x)

    # Test a common binary operator.
    tbo = TestBinaryOperator(
        arguments=['whatever', 0], value_expander=self.value_expander)
    self.assertEqual(tbo.right_operand, 0)
    self.assertEqual(tbo.args[0], 'whatever')
    tbo.Matches(DummyObject('whatever', 'id'))
    tbo.Matches(DummyObject('whatever', 'id2'))
    tbo.Matches(DummyObject('whatever', 'bg'))
    tbo.Matches(DummyObject('whatever', 'bg2'))
    self.assertListEqual(tbo.values, ['id', 'id2', 'bg', 'bg2'])

  def testContext(self):
    with self.assertRaises(errors.InvalidNumberOfOperands):
      expression_parser.Context(
          arguments=['context'], value_expander=self.value_expander)

    with self.assertRaises(errors.InvalidNumberOfOperands):
      expression_parser.Context(
          arguments=[
              'context', expression_parser.Equals(
                  arguments=['path', 'value'],
                  value_expander=self.value_expander),
              expression_parser.Equals(
                  arguments=['another_path', 'value'],
                  value_expander=self.value_expander)],
          value_expander=self.value_expander)

    # One imported_dll imports 2 functions AND one imported_dll imports
    # function RegQueryValueEx.
    arguments = [
        expression_parser.Equals(
            arguments=['imported_dlls.num_imported_functions', 1],
            value_expander=self.value_expander),
        expression_parser.Contains(
            arguments=['imported_dlls.imported_functions',
                       'RegQueryValueEx'],
            value_expander=self.value_expander)]
    condition = expression_parser.AndFilter(arguments=arguments)

    # Without context, it matches because both filters match separately.
    self.assertEqual(True, condition.Matches(self.file))

    arguments = [
        expression_parser.Equals(
            arguments=['num_imported_functions', 2],
            value_expander=self.value_expander),
        expression_parser.Contains(
            arguments=['imported_functions', 'RegQueryValueEx'],
            value_expander=self.value_expander)]
    condition = expression_parser.AndFilter(arguments=arguments)

    # The same DLL imports 2 functions AND one of these is RegQueryValueEx.
    context = expression_parser.Context(
        arguments=['imported_dlls', condition],
        value_expander=self.value_expander)

    # With context, it doesn't match because both don't match in the same dll.
    self.assertEqual(False, context.Matches(self.file))

    # One imported_dll imports only 1 function AND one imported_dll imports
    # function RegQueryValueEx.
    condition = expression_parser.AndFilter(arguments=[
        expression_parser.Equals(
            arguments=['num_imported_functions', 1],
            value_expander=self.value_expander),
        expression_parser.Contains(
            arguments=['imported_functions', 'RegQueryValueEx'],
            value_expander=self.value_expander)])

    # The same DLL imports 1 function AND it's RegQueryValueEx.
    context = expression_parser.Context(
        ['imported_dlls', condition],
        value_expander=self.value_expander)
    self.assertEqual(True, context.Matches(self.file))

    # Now test the context with a straight query.
    query = '\n'.join([
        '@imported_dlls',
        '(',
        '  imported_functions contains "RegQueryValueEx"',
        '  AND num_imported_functions == 1',
        ')'])

    parser = expression_parser.EventFilterExpressionParser(query)
    expression = parser.Parse()
    event_filter = expression.Compile(LowercaseAttributeFilterImplementation)
    self.assertEqual(True, event_filter.Matches(self.file))

  def testRegexpRaises(self):
    with self.assertRaises(ValueError):
      expression_parser.Regexp(
          arguments=['name', 'I [dont compile'],
          value_expander=self.value_expander)

  def testEscaping(self):
    parser = expression_parser.EventFilterExpressionParser(r'a is "\n"')
    expression = parser.Parse()
    self.assertEqual(expression.args[0], '\n')

    # Invalid escape sequence.
    parser = expression_parser.EventFilterExpressionParser(r'a is "\z"')
    with self.assertRaises(errors.ParseError):
      parser.Parse()

    # Can escape the backslash.
    parser = expression_parser.EventFilterExpressionParser(r'a is "\\"')
    expression = parser.Parse()
    self.assertEqual(expression.args[0], '\\')

    # Test hexadecimal escaping.

    # This fails as it's not really a hex escaped string.
    parser = expression_parser.EventFilterExpressionParser(r'a is "\xJZ"')
    with self.assertRaises(errors.ParseError):
      parser.Parse()

    # Instead, this is what one should write.
    parser = expression_parser.EventFilterExpressionParser(r'a is "\\xJZ"')
    expression = parser.Parse()
    self.assertEqual(expression.args[0], r'\xJZ')

    # Standard hex-escape.
    parser = expression_parser.EventFilterExpressionParser(
        'a is "\x41\x41\x41"')
    expression = parser.Parse()
    self.assertEqual(expression.args[0], 'AAA')

    # Hex-escape + a character.
    parser = expression_parser.EventFilterExpressionParser('a is "\x414"')
    expression = parser.Parse()
    self.assertEqual(expression.args[0], 'A4')

    # How to include r'\x41'.
    parser = expression_parser.EventFilterExpressionParser('a is "\\x41"')
    expression = parser.Parse()
    self.assertEqual(expression.args[0], '\x41')

  def testParse(self):
    # Arguments are either int, float or quoted string.
    parser = expression_parser.EventFilterExpressionParser('attribute == 1')
    expression = parser.Parse()
    self.assertIsNotNone(expression)

    parser = expression_parser.EventFilterExpressionParser('attribute == 0x10')
    expression = parser.Parse()
    self.assertIsNotNone(expression)

    parser = expression_parser.EventFilterExpressionParser('attribute == 1a')
    with self.assertRaises(errors.ParseError):
      parser.Parse()

    parser = expression_parser.EventFilterExpressionParser('attribute == 1.2')
    expression = parser.Parse()
    self.assertIsNotNone(expression)

    parser = expression_parser.EventFilterExpressionParser(
        'attribute == \'bla\'')
    expression = parser.Parse()
    self.assertIsNotNone(expression)

    parser = expression_parser.EventFilterExpressionParser('attribute == "bla"')
    expression = parser.Parse()
    self.assertIsNotNone(expression)

    parser = expression_parser.EventFilterExpressionParser('something == red')
    with self.assertRaises(errors.ParseError):
      parser.Parse()

    # Can't start with AND.
    parser = expression_parser.EventFilterExpressionParser(
        'and something is \'Blue\'')
    with self.assertRaises(errors.ParseError):
      parser.Parse()

    # Test negative filters.
    parser = expression_parser.EventFilterExpressionParser(
        'attribute not == \'dancer\'')
    with self.assertRaises(errors.ParseError):
      parser.Parse()

    parser = expression_parser.EventFilterExpressionParser(
        'attribute == not \'dancer\'')
    with self.assertRaises(errors.ParseError):
      parser.Parse()

    parser = expression_parser.EventFilterExpressionParser(
        'attribute not not equals \'dancer\'')
    with self.assertRaises(errors.ParseError):
      parser.Parse()

    parser = expression_parser.EventFilterExpressionParser('attribute not > 23')
    with self.assertRaises(errors.ParseError):
      parser.Parse()

    # Need to close braces.
    parser = expression_parser.EventFilterExpressionParser('(a is 3)')
    expression = parser.Parse()
    self.assertIsNotNone(expression)

    parser = expression_parser.EventFilterExpressionParser('(a is 3')
    with self.assertRaises(errors.ParseError):
      parser.Parse()

    # Need to open braces to close them.
    parser = expression_parser.EventFilterExpressionParser('a is 3)')
    with self.assertRaises(errors.ParseError):
      parser.Parse()

    # Context Operator alone is not accepted.
    parser = expression_parser.EventFilterExpressionParser('@attributes')
    with self.assertRaises(errors.ParseError):
      parser.Parse()

    # Accepted only with braces.
    parser = expression_parser.EventFilterExpressionParser(
        '@attributes( name is \'adrien\')')
    expression = parser.Parse()
    self.assertIsNotNone(expression)

    # Not without them.
    parser = expression_parser.EventFilterExpressionParser(
        '@attributes name is \'adrien\'')
    with self.assertRaises(errors.ParseError):
      parser.Parse()

    # Can nest context operators.
    query = '@imported_dlls( @imported_function( name is \'OpenFileA\'))'
    parser = expression_parser.EventFilterExpressionParser(query)
    expression = parser.Parse()
    self.assertIsNotNone(expression)

    # Can nest context operators and mix braces without it messing up.
    query = '@imported_dlls( @imported_function( name is \'OpenFileA\'))'
    parser = expression_parser.EventFilterExpressionParser(query)
    expression = parser.Parse()
    self.assertIsNotNone(expression)

    query = '\n'.join([
        '@imported_dlls',
        '(',
        '  @imported_function',
        '  (',
        '    name is "OpenFileA" and ordinal == 12',
        '  )',
        ')'])

    parser = expression_parser.EventFilterExpressionParser(query)
    expression = parser.Parse()
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

    parser = expression_parser.EventFilterExpressionParser(query)
    expression = parser.Parse()
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

    parser = expression_parser.EventFilterExpressionParser(query)
    with self.assertRaises(errors.ParseError):
      parser.Parse()

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

    parser = expression_parser.EventFilterExpressionParser(query)
    with self.assertRaises(errors.ParseError):
      parser.Parse()

  def testCompile(self):
    obj = DummyObject('something', 'Blue')
    parser = expression_parser.EventFilterExpressionParser(
        'something == \'Blue\'')
    expression = parser.Parse()
    event_filter = expression.Compile(LowercaseAttributeFilterImplementation)
    self.assertEqual(event_filter.Matches(obj), True)

    parser = expression_parser.EventFilterExpressionParser(
        'something == \'Red\'')
    expression = parser.Parse()
    event_filter = expression.Compile(LowercaseAttributeFilterImplementation)
    self.assertEqual(event_filter.Matches(obj), False)

    parser = expression_parser.EventFilterExpressionParser(
        'something == "Red"')
    expression = parser.Parse()
    event_filter = expression.Compile(LowercaseAttributeFilterImplementation)
    self.assertEqual(event_filter.Matches(obj), False)

    obj = DummyObject('size', 4)
    parser = expression_parser.EventFilterExpressionParser('size < 3')
    expression = parser.Parse()
    event_filter = expression.Compile(LowercaseAttributeFilterImplementation)
    self.assertEqual(event_filter.Matches(obj), False)

    parser = expression_parser.EventFilterExpressionParser('size == 4')
    expression = parser.Parse()
    event_filter = expression.Compile(LowercaseAttributeFilterImplementation)
    self.assertEqual(event_filter.Matches(obj), True)

    query = 'something is \'Blue\' and size not contains 3'
    parser = expression_parser.EventFilterExpressionParser(query)
    expression = parser.Parse()
    event_filter = expression.Compile(LowercaseAttributeFilterImplementation)
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
    parser = expression_parser.EventFilterExpressionParser(query)
    expression = parser.Parse()
    event_filter = expression.Compile(
        expression_parser.PlasoAttributeFilterImplementation)

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
    parser = expression_parser.EventFilterExpressionParser(query)
    with self.assertRaises(errors.ParseError):
      parser.Parse()

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
