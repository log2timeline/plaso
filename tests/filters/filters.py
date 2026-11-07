#!/usr/bin/env python3
"""Tests for the event filter expression parser filter classes."""

import unittest

from plaso.containers import artifacts
from plaso.containers import events
from plaso.filters import filters
from plaso.filters import value_types
from plaso.lib import definitions

from tests import test_lib as shared_test_lib
from tests.containers import test_lib as containers_test_lib


class FalseFilter(filters.Operator):
    """A filter which always evaluates to False for testing."""

    def Matches(self, event, event_data, event_data_stream, event_tag):
        """Determines if the event, data and tag match the filter.

        Args:
          event (EventObject): event to compare against the filter.
          event_data (EventData): event data to compare against the filter.
          event_data_stream (EventDataStream): event data stream.
          event_tag (EventTag): event tag to compare against the filter.

        Returns:
          bool: True if the event, data and tag match the filter, False otherwise.
        """
        return False


class TrueFilter(filters.Operator):
    """A filter which always evaluates to True for testing."""

    def Matches(self, event, event_data, event_data_stream, event_tag):
        """Determines if the event, data and tag match the filter.

        Args:
          event (EventObject): event to compare against the filter.
          event_data (EventData): event data to compare against the filter.
          event_data_stream (EventDataStream): event data stream.
          event_tag (EventTag): event tag to compare against the filter.

        Returns:
          bool: True if the event, data and tag match the filter, False otherwise.
        """
        return True


class FilterTest(shared_test_lib.BaseTestCase):
    """Tests the filter."""

    # pylint: disable=protected-access

    def testInitialize(self):
        """Tests the __init__ function."""
        filter_object = filters.Filter()
        self.assertIsNotNone(filter_object)

    def testCopyValueToString(self):
        """Tests the _CopyValueToString function."""
        filter_object = filters.Filter()

        string = filter_object._CopyValueToString(["1", "2", "3"])
        self.assertEqual(string, "123")

        string = filter_object._CopyValueToString([1, 2, 3])
        self.assertEqual(string, "123")

        string = filter_object._CopyValueToString(123)
        self.assertEqual(string, "123")

        string = filter_object._CopyValueToString(b"123")
        self.assertEqual(string, "123")

        string = filter_object._CopyValueToString("123")
        self.assertEqual(string, "123")


class AndFilterTest(shared_test_lib.BaseTestCase):
    """Tests the boolean AND filter."""

    _TEST_EVENTS = [
        {
            "data_type": "test:event",
            "test_value": 1,
            "timestamp": 5134324321,
            "timestamp_desc": definitions.TIME_DESCRIPTION_UNKNOWN,
        }
    ]

    def testMatches(self):
        """Tests the Matches function."""
        event, event_data, _ = containers_test_lib.CreateEventFromValues(
            self._TEST_EVENTS[0]
        )

        false_filter_object = FalseFilter()
        true_filter_object = TrueFilter()

        filter_object = filters.AndFilter(
            arguments=[true_filter_object, true_filter_object]
        )

        result = filter_object.Matches(event, event_data, None, None)
        self.assertTrue(result)

        filter_object = filters.AndFilter(
            arguments=[false_filter_object, true_filter_object]
        )

        result = filter_object.Matches(event, event_data, None, None)
        self.assertFalse(result)


class OrFilterTest(shared_test_lib.BaseTestCase):
    """Tests the boolean OR filter."""

    _TEST_EVENTS = [
        {
            "data_type": "test:event",
            "test_value": 1,
            "timestamp": 5134324321,
            "timestamp_desc": definitions.TIME_DESCRIPTION_UNKNOWN,
        }
    ]

    def testMatches(self):
        """Tests the Matches function."""
        event, event_data, _ = containers_test_lib.CreateEventFromValues(
            self._TEST_EVENTS[0]
        )

        false_filter_object = FalseFilter()
        true_filter_object = TrueFilter()

        filter_object = filters.OrFilter(
            arguments=[false_filter_object, true_filter_object]
        )

        result = filter_object.Matches(event, event_data, None, None)
        self.assertTrue(result)

        filter_object = filters.OrFilter(
            arguments=[false_filter_object, false_filter_object]
        )

        result = filter_object.Matches(event, event_data, None, None)
        self.assertFalse(result)


class IdentityFilterTest(shared_test_lib.BaseTestCase):
    """Tests the filter which always evaluates to True."""

    _TEST_EVENTS = [
        {
            "data_type": "test:event",
            "test_value": 1,
            "timestamp": 5134324321,
            "timestamp_desc": definitions.TIME_DESCRIPTION_UNKNOWN,
        }
    ]

    def testMatches(self):
        """Tests the Matches function."""
        event, event_data, _ = containers_test_lib.CreateEventFromValues(
            self._TEST_EVENTS[0]
        )

        filter_object = filters.IdentityFilter()

        result = filter_object.Matches(event, event_data, None, None)
        self.assertTrue(result)


class BinaryOperatorTest(shared_test_lib.BaseTestCase):
    """Tests the binary operators interface."""

    def testInitialize(self):
        """Tests the __init__ function."""
        filter_object = filters.BinaryOperator(arguments=["test_value", 1])
        self.assertIsNotNone(filter_object)


class GenericBinaryOperatorTest(shared_test_lib.BaseTestCase):
    """Tests the shared functionality for common binary operators."""

    # pylint: disable=protected-access

    _TEST_EVENTS = [
        {
            "data_type": "test:event",
            "test_value": 1,
            "timestamp": 5134324321,
            "timestamp_desc": definitions.TIME_DESCRIPTION_UNKNOWN,
        }
    ]

    def testInitialize(self):
        """Tests the __init__ function."""
        filter_object = filters.GenericBinaryOperator(arguments=["test_value", 1])
        self.assertIsNotNone(filter_object)

    def testGetTimestampBounds(self):
        """Tests the GetTimestampBounds function."""
        date_time = value_types.DateTimeValueType(1608735600000000)

        filter_object = filters.GreaterThanOperator(arguments=["timestamp", date_time])
        bounds = filter_object.GetTimestampBounds()
        self.assertEqual(bounds, (1608735599999999, None))

        filter_object = filters.LessEqualOperator(arguments=["timestamp", date_time])
        bounds = filter_object.GetTimestampBounds()
        self.assertEqual(bounds, (None, 1608735600000001))

        filter_object = filters.EqualsOperator(arguments=["timestamp", date_time])
        bounds = filter_object.GetTimestampBounds()
        self.assertEqual(bounds, (1608735599999999, 1608735600000001))

        filter_object.FlipBool()
        bounds = filter_object.GetTimestampBounds()
        self.assertEqual(bounds, (None, None))

        filter_object = filters.GreaterThanOperator(arguments=["test_value", date_time])
        bounds = filter_object.GetTimestampBounds()
        self.assertEqual(bounds, (None, None))

        filter_object = filters.NotEqualsOperator(arguments=["timestamp", date_time])
        bounds = filter_object.GetTimestampBounds()
        self.assertEqual(bounds, (None, None))

        lower_filter_object = filters.GreaterThanOperator(
            arguments=["timestamp", date_time]
        )
        upper_filter_object = filters.LessThanOperator(
            arguments=["timestamp", value_types.DateTimeValueType(1608822000000000)]
        )

        filter_object = filters.AndFilter(
            arguments=[lower_filter_object, upper_filter_object]
        )
        bounds = filter_object.GetTimestampBounds()
        self.assertEqual(bounds, (1608735599999999, 1608822000000001))

        filter_object = filters.OrFilter(
            arguments=[lower_filter_object, upper_filter_object]
        )
        bounds = filter_object.GetTimestampBounds()
        self.assertEqual(bounds, (None, None))

    def testGetValue(self):
        """Tests the _GetValue function."""
        event, event_data, _ = containers_test_lib.CreateEventFromValues(
            self._TEST_EVENTS[0]
        )

        event_tag = events.EventTag()
        event_tag.AddLabel("browser_search")

        filter_object = filters.GenericBinaryOperator(arguments=["test_value", 1])

        test_value = filter_object._GetValue(
            "test_value", event, event_data, None, event_tag
        )
        self.assertEqual(test_value, 1)

        test_value = filter_object._GetValue(
            "timestamp", event, event_data, None, event_tag
        )
        self.assertIsNotNone(test_value)
        self.assertEqual(test_value.timestamp, 5134324321)

        test_value = filter_object._GetValue("tag", event, event_data, None, event_tag)
        self.assertEqual(test_value, ["browser_search"])

    def testGetValueWithEventDataStream(self):
        """Tests the _GetValue function with alternating event data streams."""
        event, event_data, _ = containers_test_lib.CreateEventFromValues(
            self._TEST_EVENTS[0]
        )
        event_data.stream_a_value = "event_data_a"
        event_data.stream_b_value = "event_data_b"

        event_data_stream_a = events.EventDataStream()
        event_data_stream_a.stream_a_value = "stream_a"

        event_data_stream_b = events.EventDataStream()
        event_data_stream_b.stream_b_value = "stream_b"

        filter_object = filters.GenericBinaryOperator(arguments=["test_value", 1])

        expected_values = [
            (event_data_stream_a, "stream_a", "event_data_b"),
            (event_data_stream_b, "event_data_a", "stream_b"),
            (event_data_stream_a, "stream_a", "event_data_b"),
            (event_data_stream_b, "event_data_a", "stream_b"),
            (None, "event_data_a", "event_data_b"),
            (event_data_stream_a, "stream_a", "event_data_b"),
        ]
        for event_data_stream, expected_a, expected_b in expected_values:
            test_value = filter_object._GetValue(
                "stream_a_value", event, event_data, event_data_stream, None
            )
            self.assertEqual(test_value, expected_a)

            test_value = filter_object._GetValue(
                "stream_b_value", event, event_data, event_data_stream, None
            )
            self.assertEqual(test_value, expected_b)

    def testMatchesWithFalsyValue(self):
        """Tests the Matches function with a falsy event value."""
        test_values = dict(self._TEST_EVENTS[0])
        test_values["test_string"] = ""
        test_values["test_value"] = 0

        event, event_data, _ = containers_test_lib.CreateEventFromValues(test_values)

        filter_object = filters.EqualsOperator(arguments=["test_value", 0])
        result = filter_object.Matches(event, event_data, None, None)
        self.assertTrue(result)

        filter_object.FlipBool()
        result = filter_object.Matches(event, event_data, None, None)
        self.assertFalse(result)

        filter_object = filters.LessThanOperator(arguments=["test_value", 5])
        result = filter_object.Matches(event, event_data, None, None)
        self.assertTrue(result)

        filter_object = filters.EqualsOperator(arguments=["test_string", ""])
        result = filter_object.Matches(event, event_data, None, None)
        self.assertTrue(result)

        filter_object = filters.NotEqualsOperator(arguments=["test_string", "foo"])
        result = filter_object.Matches(event, event_data, None, None)
        self.assertTrue(result)

    # TODO: add tests for FlipBool function


class EqualsOperatorTest(shared_test_lib.BaseTestCase):
    """Tests the equals operator."""

    # pylint: disable=protected-access

    def testCompareValue(self):
        """Tests the _CompareValue function."""
        filter_object = filters.EqualsOperator(arguments=["first", "second"])

        result = filter_object._CompareValue(0, 10)
        self.assertFalse(result)

        result = filter_object._CompareValue(10, 10)
        self.assertTrue(result)


class NotEqualsOperatorTest(shared_test_lib.BaseTestCase):
    """Tests the not equals operator."""

    # pylint: disable=protected-access

    def testCompareValue(self):
        """Tests the _CompareValue function."""
        filter_object = filters.NotEqualsOperator(arguments=["first", "second"])

        result = filter_object._CompareValue(0, 10)
        self.assertTrue(result)

        result = filter_object._CompareValue(10, 10)
        self.assertFalse(result)


class LessThanOperatorTest(shared_test_lib.BaseTestCase):
    """Tests the less than operator."""

    # pylint: disable=protected-access

    def testCompareValue(self):
        """Tests the _CompareValue function."""
        filter_object = filters.LessThanOperator(arguments=["first", "second"])

        result = filter_object._CompareValue(0, 10)
        self.assertTrue(result)

        result = filter_object._CompareValue(10, 10)
        self.assertFalse(result)

        result = filter_object._CompareValue(20, 10)
        self.assertFalse(result)


class LessEqualOperatorTest(shared_test_lib.BaseTestCase):
    """Tests the less equal operator."""

    # pylint: disable=protected-access

    def testCompareValue(self):
        """Tests the _CompareValue function."""
        filter_object = filters.LessEqualOperator(arguments=["first", "second"])

        result = filter_object._CompareValue(0, 10)
        self.assertTrue(result)

        result = filter_object._CompareValue(10, 10)
        self.assertTrue(result)

        result = filter_object._CompareValue(20, 10)
        self.assertFalse(result)


class GreaterThanOperatorTest(shared_test_lib.BaseTestCase):
    """Tests the greater than operator."""

    # pylint: disable=protected-access

    def testCompareValue(self):
        """Tests the _CompareValue function."""
        filter_object = filters.GreaterThanOperator(arguments=["first", "second"])

        result = filter_object._CompareValue(0, 10)
        self.assertFalse(result)

        result = filter_object._CompareValue(10, 10)
        self.assertFalse(result)

        result = filter_object._CompareValue(20, 10)
        self.assertTrue(result)


class GreaterEqualOperatorTest(shared_test_lib.BaseTestCase):
    """Tests the greater equal operator."""

    # pylint: disable=protected-access

    def testCompareValue(self):
        """Tests the _CompareValue function."""
        filter_object = filters.GreaterEqualOperator(arguments=["first", "second"])

        result = filter_object._CompareValue(0, 10)
        self.assertFalse(result)

        result = filter_object._CompareValue(10, 10)
        self.assertTrue(result)

        result = filter_object._CompareValue(20, 10)
        self.assertTrue(result)


class ContainsOperatorTest(shared_test_lib.BaseTestCase):
    """Tests the contains operator."""

    # pylint: disable=protected-access

    def testCompareValue(self):
        """Tests the _CompareValue function."""
        filter_object = filters.Contains(arguments=["first", "second"])

        # Test a case insensitive string comparison.
        result = filter_object._CompareValue("Some Text", "text")
        self.assertTrue(result)

        result = filter_object._CompareValue("Some Text", "other")
        self.assertFalse(result)

        # Test a case sensitive comparison of non-string values.
        result = filter_object._CompareValue(b"Some Text", b"Text")
        self.assertTrue(result)

        result = filter_object._CompareValue(b"Some Text", b"text")
        self.assertFalse(result)

        result = filter_object._CompareValue(["first", "second"], "second")
        self.assertTrue(result)

        # Test values that cannot be compared.
        result = filter_object._CompareValue(10, "1")
        self.assertFalse(result)

        result = filter_object._CompareValue("Some Text", 1)
        self.assertFalse(result)

        # Test a path artifact.
        path_artifact = artifacts.PathArtifact(
            path="Windows\\System32", path_segment_separator="\\"
        )

        result = filter_object._CompareValue(
            "C:\\Windows\\System32\\cmd.exe", path_artifact
        )
        self.assertTrue(result)

        result = filter_object._CompareValue("C:\\Windows\\cmd.exe", path_artifact)
        self.assertFalse(result)

        result = filter_object._CompareValue(10, path_artifact)
        self.assertFalse(result)


class InSetOperatorTest(shared_test_lib.BaseTestCase):
    """Tests the in set operator."""

    # pylint: disable=protected-access

    def testCompareValue(self):
        """Tests the _CompareValue function."""
        filter_object = filters.InSet(arguments=["first", "second"])

        result = filter_object._CompareValue("first", ["first", "second"])
        self.assertTrue(result)

        result = filter_object._CompareValue("third", ["first", "second"])
        self.assertFalse(result)

        # Test that the characters of a string are not compared individually.
        result = filter_object._CompareValue("fs", ["f", "s"])
        self.assertFalse(result)

        # Test an iterable event value.
        result = filter_object._CompareValue(["first"], ["first", "second"])
        self.assertTrue(result)

        result = filter_object._CompareValue(["first", "third"], ["first", "second"])
        self.assertFalse(result)

        # Test an event value that is not iterable.
        result = filter_object._CompareValue(10, ["first", "second"])
        self.assertFalse(result)


class RegexpOperatorTest(shared_test_lib.BaseTestCase):
    """Tests the regular expression operator."""

    # pylint: disable=protected-access

    def testInitialize(self):
        """Tests the __init__ function."""
        filter_object = filters.Regexp(arguments=["first", "Te.t"])
        self.assertIsNotNone(filter_object.compiled_re)

        with self.assertRaises(ValueError):
            filters.Regexp(arguments=["first", "("])

    def testCompareValue(self):
        """Tests the _CompareValue function."""
        filter_object = filters.Regexp(arguments=["first", "Te.t"])

        result = filter_object._CompareValue("Some Text", None)
        self.assertTrue(result)

        # Test that the comparison is case sensitive.
        result = filter_object._CompareValue("Some text", None)
        self.assertFalse(result)

        # Test that "." matches a newline.
        result = filter_object._CompareValue("Te\nt", None)
        self.assertTrue(result)

        result = filter_object._CompareValue(b"Some Text", None)
        self.assertTrue(result)

        result = filter_object._CompareValue(["Te", "xt"], None)
        self.assertTrue(result)

        # Test a value that cannot be converted to a string.
        result = filter_object._CompareValue(None, None)
        self.assertFalse(result)


class RegexpInsensitiveOperatorTest(shared_test_lib.BaseTestCase):
    """Tests the case insensitive regular expression operator."""

    # pylint: disable=protected-access

    def testInitialize(self):
        """Tests the __init__ function."""
        filter_object = filters.RegexpInsensitive(arguments=["first", "Te.t"])
        self.assertIsNotNone(filter_object.compiled_re)

        with self.assertRaises(ValueError):
            filters.RegexpInsensitive(arguments=["first", "["])

    def testCompareValue(self):
        """Tests the _CompareValue function."""
        filter_object = filters.RegexpInsensitive(arguments=["first", "Te.t"])

        result = filter_object._CompareValue("Some Text", None)
        self.assertTrue(result)

        # Test that the comparison is case insensitive.
        result = filter_object._CompareValue("SOME TEXT", None)
        self.assertTrue(result)

        # Test that "." matches a newline.
        result = filter_object._CompareValue("te\nt", None)
        self.assertTrue(result)

        result = filter_object._CompareValue("Some Tet", None)
        self.assertFalse(result)


if __name__ == "__main__":
    unittest.main()
