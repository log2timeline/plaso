#!/usr/bin/env python3
"""Tests for the event filter functions."""

import re
import unittest

from dfdatetime import posix_time as dfdatetime_posix_time
from dfdatetime import time_elements as dfdatetime_time_elements

from plaso.containers import events
from plaso.filters import expression_parser
from plaso.filters import expressions
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
        super().__init__(arguments=arguments, **kwargs)
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
        token = expression_parser.Token("STRING", r"\\(.)", "StringEscape", None)
        self.assertIsNotNone(token)


class EventFilterExpressionParserTest(shared_test_lib.BaseTestCase):
    """Tests the event filter expression parser."""

    # pylint: disable=protected-access

    _TEST_EVENTS = [
        {
            "_parser_chain": "test_parser",
            "data_type": "test_log:entry",
            "display_name": (
                "unknown:/My Documents/goodfella/Documents/Hideout/myfile.txt"
            ),
            "filename": "/My Documents/goodfella/Documents/Hideout/myfile.txt",
            "hostname": "Agrabah",
            "inode": 1245,
            "text": "User did a very bad thing, bad, bad thing that awoke Dr. Evil.",
            "text_short": "This description is different than the long one.",
            "timestamp": "2015-11-18 01:15:43",
            "timestamp_desc": "Last Written",
        }
    ]

    def _CheckIfExpressionMatches(
        self,
        expression,
        event,
        event_data,
        event_data_stream,
        event_tag,
        expected_result,
    ):
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

        result = event_filter.Matches(event, event_data, event_data_stream, event_tag)
        self.assertEqual(expected_result, result)

    def testAddArgument(self):
        """Tests the _AddArgument function."""
        parser = expression_parser.EventFilterExpressionParser()
        parser._Reset()

        parser._SetAttribute(string="attribute")
        parser._SetOperator(string="is")
        current_expression = parser._current_expression

        next_state = parser._AddArgument(1)
        self.assertEqual(next_state, "BINARY")
        self.assertEqual(len(parser._stack), 1)
        self.assertIs(parser._stack[0], current_expression)
        self.assertEqual(parser._stack[0].args, [1])
        self.assertIsNot(parser._current_expression, current_expression)
        self.assertEqual(parser._current_expression.args, [])

        # Test an operator that supports negation.
        parser._Reset()
        parser._SetAttribute(string="attribute")
        parser._SetOperator(string="is")
        parser._have_negate_keyword = True

        next_state = parser._AddArgument(1)
        self.assertEqual(next_state, "BINARY")

        # Test an operator that does not support negation.
        parser._Reset()
        parser._SetAttribute(string="attribute")
        parser._SetOperator(string="<")
        parser._have_negate_keyword = True

        with self.assertRaises(errors.ParseError):
            parser._AddArgument(1)

    def testAddArgumentDateTime(self):
        """Tests the _AddArgumentDateTime function."""
        parser = expression_parser.EventFilterExpressionParser()

        # Test a POSIX timestamp in microseconds.
        parser._Reset()
        parser._datetime_value = 1447809343000000

        next_state = parser._AddArgumentDateTime()
        self.assertEqual(next_state, "BINARY")
        self.assertIsNone(parser._datetime_value)

        date_time = parser._stack[0].args[0]
        self.assertIsInstance(date_time, dfdatetime_posix_time.PosixTimeInMicroseconds)
        self.assertEqual(date_time.timestamp, 1447809343000000)

        # Test an ISO 8601 date and time string.
        parser._Reset()
        parser._datetime_value = "2015-11-18T01:15:43.123456"

        next_state = parser._AddArgumentDateTime()
        self.assertEqual(next_state, "BINARY")

        date_time = parser._stack[0].args[0]
        self.assertIsInstance(
            date_time, dfdatetime_time_elements.TimeElementsInMicroseconds
        )
        self.assertEqual(date_time.CopyToDateTimeString(), "2015-11-18 01:15:43.123456")

        # Test an unsupported ISO 8601 date and time string.
        parser._Reset()
        parser._datetime_value = "bogus"

        with self.assertRaises(errors.ParseError):
            parser._AddArgumentDateTime()

        # Test an unsupported date and time value.
        parser._Reset()
        parser._datetime_value = None

        with self.assertRaises(errors.ParseError):
            parser._AddArgumentDateTime()

    def testAddArgumentDecimalInteger(self):
        """Tests the _AddArgumentDecimalInteger function."""
        parser = expression_parser.EventFilterExpressionParser()
        parser._Reset()

        next_state = parser._AddArgumentDecimalInteger(string="10")
        self.assertEqual(next_state, "BINARY")
        self.assertEqual(parser._stack[0].args, [10])
        self.assertIsInstance(parser._stack[0].args[0], int)

        parser._Reset()

        with self.assertRaises(errors.ParseError):
            parser._AddArgumentDecimalInteger(string="1a")

        self.assertEqual(parser._stack, [])

    def testAddArgumentFloatingPoint(self):
        """Tests the _AddArgumentFloatingPoint function."""
        parser = expression_parser.EventFilterExpressionParser()
        parser._Reset()

        next_state = parser._AddArgumentFloatingPoint(string="1.5")
        self.assertEqual(next_state, "BINARY")
        self.assertEqual(parser._stack[0].args, [1.5])
        self.assertIsInstance(parser._stack[0].args[0], float)

        parser._Reset()

        with self.assertRaises(errors.ParseError):
            parser._AddArgumentFloatingPoint(string="x")

        self.assertEqual(parser._stack, [])

    def testAddArgumentHexadecimalInteger(self):
        """Tests the _AddArgumentHexadecimalInteger function."""
        parser = expression_parser.EventFilterExpressionParser()
        parser._Reset()

        next_state = parser._AddArgumentHexadecimalInteger(string="0x10")
        self.assertEqual(next_state, "BINARY")
        self.assertEqual(parser._stack[0].args, [16])

        parser._Reset()

        next_state = parser._AddArgumentHexadecimalInteger(string="0xff")
        self.assertEqual(next_state, "BINARY")
        self.assertEqual(parser._stack[0].args, [255])

        parser._Reset()

        with self.assertRaises(errors.ParseError):
            parser._AddArgumentHexadecimalInteger(string="0xzz")

        self.assertEqual(parser._stack, [])

    def testAddBinaryOperator(self):
        """Tests the _AddBinaryOperator function."""
        parser = expression_parser.EventFilterExpressionParser()
        parser._Reset()

        next_state = parser._AddBinaryOperator(string="&&")
        self.assertIsNone(next_state)
        self.assertIsNotNone(parser._stack[0])

    def testAddBracketClose(self):
        """Tests the _AddBracketClose function."""
        parser = expression_parser.EventFilterExpressionParser()
        parser._Reset()

        next_state = parser._AddBracketClose()
        self.assertIsNone(next_state)
        self.assertEqual(parser._stack[0], ")")

    def testAddBracketOpen(self):
        """Tests the _AddBracketOpen function."""
        parser = expression_parser.EventFilterExpressionParser()
        parser._Reset()

        next_state = parser._AddBracketOpen()
        self.assertIsNone(next_state)
        self.assertEqual(parser._stack[0], "(")

    def testCombineBinaryExpressions(self):
        """Tests the _CombineBinaryExpressions function."""
        parser = expression_parser.EventFilterExpressionParser()
        parser._Reset()

        left_expression = expressions.EventExpression()
        right_expression = expressions.EventExpression()
        binary_expression = expressions.BinaryExpression(operator="and")
        parser._stack = [left_expression, binary_expression, right_expression]

        # Test an operator that is not on the stack.
        parser._CombineBinaryExpressions("or")
        self.assertEqual(len(parser._stack), 3)
        self.assertEqual(binary_expression.args, [])

        # Test an operator that is on the stack, compared case insensitive.
        parser._CombineBinaryExpressions("AND")
        self.assertEqual(len(parser._stack), 1)
        self.assertIs(parser._stack[0], binary_expression)
        self.assertEqual(binary_expression.args, [left_expression, right_expression])

        # Test an operator without an expression on both sides.
        binary_expression = expressions.BinaryExpression(operator="and")
        parser._stack = ["(", binary_expression, right_expression]

        parser._CombineBinaryExpressions("and")
        self.assertEqual(len(parser._stack), 3)
        self.assertEqual(binary_expression.args, [])

    def testCombineParenthesis(self):
        """Tests the _CombineParenthesis function."""
        parser = expression_parser.EventFilterExpressionParser()
        parser._Reset()

        parser._CombineParenthesis()

        parser._AddBracketOpen()
        parser._AddBinaryOperator(string="&&")
        parser._AddBracketClose()
        self.assertEqual(len(parser._stack), 3)

        parser._CombineParenthesis()
        self.assertEqual(len(parser._stack), 1)

    def testGetNextToken(self):
        """Tests the _GetNextToken function."""
        parser = expression_parser.EventFilterExpressionParser()
        parser._Reset()

        parser._buffer = ""
        token = parser._GetNextToken()
        self.assertIsNone(token)

        parser._buffer = "("
        token = parser._GetNextToken()
        self.assertIsNotNone(token)
        self.assertEqual(parser._buffer, "")
        self.assertEqual(parser._processed_buffer, "(")

    def testNegateExpression(self):
        """Tests the _NegateExpression function."""
        parser = expression_parser.EventFilterExpressionParser()
        parser._Reset()

        parser._SetOperator(string="is")
        self.assertTrue(parser._current_expression._bool_value)

        parser._NegateExpression()
        self.assertTrue(parser._have_negate_keyword)
        self.assertFalse(parser._current_expression._bool_value)

        # Test negation that is expressed more than once.
        with self.assertRaises(errors.ParseError):
            parser._NegateExpression()

        # Test an operator that does not support negation.
        parser._Reset()
        parser._SetOperator(string="<")

        with self.assertRaises(errors.ParseError):
            parser._NegateExpression()

        self.assertFalse(parser._have_negate_keyword)

        # Test negation after an argument.
        parser._Reset()
        parser._current_expression.args.append(1)

        with self.assertRaises(errors.ParseError):
            parser._NegateExpression()

    def testNoOperation(self):
        """Tests the _NoOperation function."""
        parser = expression_parser.EventFilterExpressionParser()

        parser._NoOperation()

    def testPopState(self):
        """Tests the _PopState function."""
        parser = expression_parser.EventFilterExpressionParser()
        parser._Reset()

        parser._state_stack.append("INITIAL")
        self.assertEqual(len(parser._state_stack), 1)

        next_state = parser._PopState()
        self.assertEqual(next_state, "INITIAL")
        self.assertEqual(len(parser._state_stack), 0)

        with self.assertRaises(errors.ParseError):
            parser._PopState()

    def testPushBack(self):
        """Tests the _PushBack function."""
        parser = expression_parser.EventFilterExpressionParser()
        parser._Reset()

        parser._buffer = ""
        parser._processed_buffer = "mytest"

        next_state = parser._PushBack(string="test")
        self.assertIsNone(next_state)
        self.assertEqual(parser._buffer, "test")
        self.assertEqual(parser._processed_buffer, "my")

    def testPushState(self):
        """Tests the _PushState function."""
        parser = expression_parser.EventFilterExpressionParser()
        parser._Reset()

        parser._state = "INITIAL"
        self.assertEqual(len(parser._state_stack), 0)

        next_state = parser._PushState()
        self.assertIsNone(next_state)
        self.assertEqual(len(parser._state_stack), 1)
        self.assertEqual(parser._state_stack[0], "INITIAL")
        self.assertEqual(parser._state, "INITIAL")

    def testReduce(self):
        """Tests the _Reduce function."""
        parser = expression_parser.EventFilterExpressionParser()
        parser._Reset()

        left_expression = expressions.EventExpression()
        right_expression = expressions.EventExpression()
        binary_expression = expressions.BinaryExpression(operator="or")
        parser._stack = [
            "(",
            left_expression,
            binary_expression,
            right_expression,
            ")",
        ]
        parser._state = "BINARY"

        expression = parser._Reduce()
        self.assertIs(expression, binary_expression)
        self.assertEqual(expression.args, [left_expression, right_expression])

        # Test an unsupported state.
        parser._Reset()
        parser._stack = [expressions.EventExpression()]
        parser._state = "ARGUMENT"

        with self.assertRaises(errors.ParseError):
            parser._Reduce()

        # Test a stack that cannot be reduced to a single expression.
        parser._Reset()
        parser._stack = [
            expressions.EventExpression(),
            expressions.EventExpression(),
        ]

        with self.assertRaises(errors.ParseError):
            parser._Reduce()

    def testReset(self):
        """Tests the _Reset function."""
        parser = expression_parser.EventFilterExpressionParser()
        parser._Reset()

    def testSetAttribute(self):
        """Tests the _SetAttribute function."""
        parser = expression_parser.EventFilterExpressionParser()
        parser._Reset()

        next_state = parser._SetAttribute(string="attribute")
        self.assertEqual(next_state, "OPERATOR")

    def testSetOperator(self):
        """Tests the _SetOperator function."""
        parser = expression_parser.EventFilterExpressionParser()
        parser._Reset()

        self.assertIsNotNone(parser._current_expression)
        self.assertIsNone(parser._current_expression.operator)

        next_state = parser._SetOperator(string="&&")
        self.assertIsNone(next_state)
        self.assertEqual(parser._current_expression.operator, "&&")

    def testStringEscape(self):
        """Tests the _StringEscape function."""
        parser = expression_parser.EventFilterExpressionParser()
        parser._Reset()

        parser._StringStart()
        self.assertEqual(parser._string, "")

        match = re.compile(r"\\(.)").match("\\n")
        next_state = parser._StringEscape(string="\\n", match=match)
        self.assertIsNone(next_state)
        self.assertEqual(parser._string, "\n")

        with self.assertRaises(errors.ParseError):
            match = re.compile(r"\\(.)").match("\\q")
            parser._StringEscape(string="\\q", match=match)

    def testStringExpand(self):
        """Tests the _StringExpand function."""
        parser = expression_parser.EventFilterExpressionParser()
        parser._Reset()

        parser._StringStart()
        self.assertEqual(parser._string, "")

        next_state = parser._StringExpand(string="string")
        self.assertIsNone(next_state)
        self.assertEqual(parser._string, "string")

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
        self.assertEqual(parser._string, "")

    # TODO: add tests for HexEscape

    def testParse(self):
        """Tests the Parse function."""
        parser = expression_parser.EventFilterExpressionParser()

        # Arguments are either int, float or quoted string.
        expression = parser.Parse("attribute == 1")
        self.assertIsNotNone(expression)

        expression = parser.Parse("attribute == 0x10")
        self.assertIsNotNone(expression)

        with self.assertRaises(errors.ParseError):
            parser.Parse("attribute == 1a")

        expression = parser.Parse("attribute == 1.2")
        self.assertIsNotNone(expression)

        expression = parser.Parse("attribute == 'bla'")
        self.assertIsNotNone(expression)

        expression = parser.Parse('attribute == "bla"')
        self.assertIsNotNone(expression)

        with self.assertRaises(errors.ParseError):
            parser.Parse("something == red")

        # Test expression starting with AND.
        with self.assertRaises(errors.ParseError):
            parser.Parse("and something is 'Blue'")

        # Test incorrect usage of NOT.
        with self.assertRaises(errors.ParseError):
            parser.Parse("attribute not == 'dancer'")

        with self.assertRaises(errors.ParseError):
            parser.Parse("attribute == not 'dancer'")

        with self.assertRaises(errors.ParseError):
            parser.Parse("attribute not not equals 'dancer'")

        with self.assertRaises(errors.ParseError):
            parser.Parse("attribute not > 23")

        # Test double negative matching.
        with self.assertRaises(errors.ParseError):
            parser.Parse("filename not not contains 'GoodFella'")

    def testParseWithBraces(self):
        """Tests the Parse function with braces."""
        parser = expression_parser.EventFilterExpressionParser()

        expression = parser.Parse("(a is 3)")
        self.assertIsNotNone(expression)

        # Need to close braces.
        with self.assertRaises(errors.ParseError):
            parser.Parse("(a is 3")

        # Need to open braces to close them.
        with self.assertRaises(errors.ParseError):
            parser.Parse("a is 3)")

    def testParseWithEscaping(self):
        """Tests the Parse function with escaping."""
        parser = expression_parser.EventFilterExpressionParser()

        expression = parser.Parse(r'a is "\n"')
        self.assertEqual(expression.args[0], "\n")

        # Can escape the backslash.
        expression = parser.Parse(r'a is "\\"')
        self.assertEqual(expression.args[0], "\\")

        # Invalid escape sequence.
        with self.assertRaises(errors.ParseError):
            parser.Parse(r'a is "\z"')

    def testParseWithHexadecimalEscaping(self):
        """Tests the Parse function with hexadecimal escaping."""
        parser = expression_parser.EventFilterExpressionParser()

        # Instead, this is what one should write.
        expression = parser.Parse(r'a is "\\xJZ"')
        self.assertEqual(expression.args[0], r"\xJZ")

        # Standard hex-escape.
        expression = parser.Parse('a is "\x41\x41\x41"')
        self.assertEqual(expression.args[0], "AAA")

        # Hex-escape + a character.
        expression = parser.Parse('a is "\x414"')
        self.assertEqual(expression.args[0], "A4")

        # How to include r'\x41'.
        expression = parser.Parse('a is "\\x41"')
        self.assertEqual(expression.args[0], "\x41")

        # This fails as it's not really a hex escaped string.
        with self.assertRaises(errors.ParseError):
            parser.Parse(r'a is "\xJZ"')

    def testParseWithEvents(self):
        """Tests the Parse function with events."""
        event, event_data, _ = containers_test_lib.CreateEventFromValues(
            self._TEST_EVENTS[0]
        )

        event_tag = events.EventTag()
        event_tag.AddLabel("browser_search")

        self._CheckIfExpressionMatches(
            "filename contains 'GoodFella'", event, event_data, None, event_tag, True
        )

        # Test timestamp filtering.
        self._CheckIfExpressionMatches(
            "timestamp >= '2015-11-18'", event, event_data, None, event_tag, True
        )

        self._CheckIfExpressionMatches(
            "timestamp < '2015-11-19'", event, event_data, None, event_tag, True
        )

        expression = (
            "timestamp < '2015-11-18T01:15:44.341' and "
            "timestamp > '2015-11-18 01:15:42'"
        )

        self._CheckIfExpressionMatches(
            expression, event, event_data, None, event_tag, True
        )

        self._CheckIfExpressionMatches(
            "timestamp > '2015-11-19'", event, event_data, None, event_tag, False
        )

        # Perform few attribute tests.
        self._CheckIfExpressionMatches(
            "filename not contains 'sometext'", event, event_data, None, event_tag, True
        )

        expression = (
            "timestamp_desc CONTAINS 'written' AND timestamp > '2015-11-18' "
            "AND timestamp < '2015-11-25 12:56:21'"
        )

        self._CheckIfExpressionMatches(
            expression, event, event_data, None, event_tag, True
        )

        self._CheckIfExpressionMatches(
            "tag contains 'browser_search'", event, event_data, None, event_tag, True
        )

        # Test multiple attributes.
        self._CheckIfExpressionMatches(
            "text iregexp 'bad, bad thing [a-zA-Z\\\\s.]+ evil'",
            event,
            event_data,
            None,
            event_tag,
            True,
        )


if __name__ == "__main__":
    unittest.main()
