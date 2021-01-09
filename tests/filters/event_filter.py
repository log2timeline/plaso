#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""Tests for the event object filter."""

import unittest

from plaso.containers import events
from plaso.filters import event_filter
from plaso.lib import errors

from tests.filters import test_lib


class EventObjectFilterTest(test_lib.FilterTestCase):
  """Tests for the event object filter."""

  def testCompilerFilter(self):
    """Tests the CompileFilter function."""
    test_filter = event_filter.EventObjectFilter()

    test_filter.CompileFilter(
        'some_stuff is "random" and other_stuff is not "random"')

    test_filter.CompileFilter('timestamp is "2020-12-23 15:00:00"')

    test_filter.CompileFilter('timestamp is DATETIME("2020-12-23T15:00:00")')

    test_filter.CompileFilter('filename contains PATH("/etc/issue")')

    with self.assertRaises(errors.ParseError):
      test_filter.CompileFilter(
          'SELECT stuff FROM machine WHERE conditions are met')

    with self.assertRaises(errors.ParseError):
      test_filter.CompileFilter(
          '/tmp/file_that_most_likely_does_not_exist')

    with self.assertRaises(errors.ParseError):
      test_filter.CompileFilter(
          'some random stuff that is destined to fail')

    with self.assertRaises(errors.ParseError):
      test_filter.CompileFilter(
          'some_stuff is "random" and other_stuff ')

  def testMatch(self):
    """Tests the Match function."""
    test_filter = event_filter.EventObjectFilter()
    test_filter.CompileFilter('timestamp is DATETIME("2020-12-23T15:00:00")')

    event = events.EventObject()
    event.timestamp = 1608735600000000

    result = test_filter.Match(event, None, None, None)
    self.assertTrue(result)

    test_filter = event_filter.EventObjectFilter()
    test_filter.CompileFilter('filename contains PATH("etc/issue")')

    event_data = events.EventData()
    event_data.filename = '/usr/local/etc/issue'

    result = test_filter.Match(None, event_data, None, None)
    self.assertTrue(result)

    event_data.filename = '/etc/issue.net'

    result = test_filter.Match(None, event_data, None, None)
    self.assertFalse(result)


if __name__ == '__main__':
  unittest.main()
