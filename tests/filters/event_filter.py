#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""Tests for the event object filter."""

from __future__ import unicode_literals

import unittest

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


if __name__ == '__main__':
  unittest.main()
