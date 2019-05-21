#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""Tests for the event filter expression parser value expander classes."""

from __future__ import unicode_literals

import unittest

from plaso.filters import value_expanders

from tests import test_lib as shared_test_lib
from tests.filters import test_lib


class EventValueExpanderTest(shared_test_lib.BaseTestCase):
  """Tests the value expander for event filters."""

  # TODO: add tests for _GetMessage
  # TODO: add tests for _GetSources
  # TODO: add tests for _GetValue

  def testExpand(self):
    """Tests the Expand function."""
    test_expander = value_expanders.EventValueExpander()

    test_object = test_lib.DummyFile()

    # Test case insensitivity of value names.
    values_lowercase = test_expander.Expand(test_object, 'size')
    values_uppercase = test_expander.Expand(test_object, 'Size')
    self.assertListEqual(list(values_lowercase), list(values_uppercase))

    # Existing, non-repeated, leaf is a value.
    values = test_expander.Expand(test_object, 'size')
    self.assertListEqual(list(values), [10])

    # Existing, non-repeated, leaf is iterable.
    values = test_expander.Expand(test_object, 'attributes')
    self.assertListEqual(list(values), [['Backup', 'Archive']])

    # Existing, repeated, leaf is value.
    values = test_expander.Expand(test_object, 'hash.md5')
    self.assertListEqual(list(values), ['123abc', '456def'])

    # Existing, repeated, leaf is iterable.
    values = test_expander.Expand(test_object, 'non_callable_repeated.desmond')
    self.assertListEqual(
        list(values), [['brotha', 'brotha'], ['brotha', 'sista']])

    # Now with an iterator.
    values = test_expander.Expand(test_object, 'deferred_values')
    self.assertListEqual([list(value) for value in values], [['a', 'b']])

    # Iterator > generator.
    values = test_expander.Expand(
        test_object, 'imported_dlls.imported_functions')
    expected = [['FindWindow', 'CreateFileA'], ['RegQueryValueEx']]
    self.assertListEqual([list(value) for value in values], expected)

    # Non-existing first path.
    values = test_expander.Expand(test_object, 'nonexistant')
    self.assertListEqual(list(values), [])

    # Non-existing in the middle.
    values = test_expander.Expand(test_object, 'hash.mink.boo')
    self.assertListEqual(list(values), [])

    # Non-existing as a leaf.
    values = test_expander.Expand(test_object, 'hash.mink')
    self.assertListEqual(list(values), [])

    # Non-callable leaf.
    values = test_expander.Expand(test_object, 'non_callable_leaf')
    self.assertListEqual(list(values), ['yoda'])

    # callable.
    values = test_expander.Expand(test_object, 'Callable')
    self.assertListEqual(list(values), [])

    # leaf under a callable. Will return nothing.
    values = test_expander.Expand(test_object, 'Callable.a')
    self.assertListEqual(list(values), [])


if __name__ == "__main__":
  unittest.main()
