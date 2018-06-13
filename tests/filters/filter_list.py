#!/usr/bin/env python
# -*- coding: utf-8 -*-
"""Tests for list of object filters."""

from __future__ import unicode_literals

import os
import codecs
import tempfile
import unittest

from plaso.filters import filter_list
from plaso.lib import errors

from tests.filters import test_lib


class ObjectFilterTest(test_lib.FilterTestCase):
  """Tests for the list of object filters."""

  def _CreateFilterFileAndCompileFilter(self, test_filter, content):
    """Creates a filter file and compiles the filter based on the file.

    Args:
      test_filter (FilterObject): the test filter object).
      content(str): the content of the filter file.
    """
    # The temporary file needs to be closed to make sure the content
    # was been written.
    with tempfile.NamedTemporaryFile(delete=False) as temporary_file:
      temporary_file_path = temporary_file.name
      content_bytes = codecs.encode(content, 'utf-8')
      temporary_file.write(content_bytes)

    try:
      test_filter.CompileFilter(temporary_file_path)
    finally:
      os.remove(temporary_file_path)

  def testCompilerFilter(self):
    """Tests the CompileFilter function."""
    test_filter = filter_list.ObjectFilterList()

    with self.assertRaises(errors.WrongPlugin):
      test_filter.CompileFilter(
          'SELECT stuff FROM machine WHERE conditions are met')

    with self.assertRaises(errors.WrongPlugin):
      test_filter.CompileFilter(
          '/tmp/file_that_most_likely_does_not_exist')

    with self.assertRaises(errors.WrongPlugin):
      test_filter.CompileFilter(
          'some random stuff that is destined to fail')

    with self.assertRaises(errors.WrongPlugin):
      test_filter.CompileFilter(
          'some_stuff is "random" and other_stuff ')

    with self.assertRaises(errors.WrongPlugin):
      test_filter.CompileFilter(
          'some_stuff is "random" and other_stuff is not "random"')

  def testCompilerFilterWithFilterFile(self):
    """Tests the CompileFilter function with a filter file."""
    test_filter = filter_list.ObjectFilterList()

    one_rule = '\n'.join([
        'Again_Dude:',
        '  description: Heavy artillery caught on fire',
        '  case_nr: 62345',
        '  analysts: [anonymous]',
        '  urls: [cnn.com,microsoft.com]',
        '  filter: message contains "dude where is my car"'])

    self._CreateFilterFileAndCompileFilter(test_filter, one_rule)

    collection = '\n'.join([
        'Rule_Dude:',
        '    description: This is the very case I talk about, a lot',
        '    case_nr: 1235',
        '    analysts: [dude, jack, horn]',
        '    urls: [mbl.is,visir.is]',
        ('    filter: date > "2012-01-01 10:54:13" and parser not contains '
         '"evtx"'),
        '',
        'Again_Dude:',
        '  description: Heavy artillery caught on fire',
        '  case_nr: 62345',
        '  analysts: [smith, perry, john]',
        '  urls: [cnn.com,microsoft.com]',
        '  filter: message contains "dude where is my car"',
        '',
        'Third_Rule_Of_Thumb:',
        '    description: Another ticket for another day.',
        '    case_nr: 234',
        '    analysts: [joe]',
        '    urls: [mbl.is,symantec.com/whereevillies,virustotal.com/myhash]',
        '    filter: evil_bit is 1'])

    self._CreateFilterFileAndCompileFilter(test_filter, collection)


if __name__ == '__main__':
  unittest.main()
