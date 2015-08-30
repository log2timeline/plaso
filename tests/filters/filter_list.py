#!/usr/bin/python
# -*- coding: utf-8 -*-
"""Tests for list of object filters."""

import os
import tempfile
import unittest

from plaso.filters import filter_list
from plaso.lib import errors

from tests.filters import test_lib


class ObjectFilterTest(test_lib.FilterTestCase):
  """Tests for the list of object filters."""

  def _CreateFileAndTest(self, test_filter, content):
    """Creates a filter file and then runs the test.

    Args:
      test_filter: the test filter object (instance of FilterObject).
      content: the content of the filter file.
    """
    # The temporary file needs to be closed to make sure the content
    # was been written.
    temporary_file_path = u''
    with tempfile.NamedTemporaryFile(delete=False) as temporary_file:
      temporary_file_path = temporary_file.name
      temporary_file.write(content)

    try:
      test_filter.CompileFilter(temporary_file_path)
    finally:
      os.remove(temporary_file_path)

  def testCompilerFilter(self):
    """Tests the CompileFilter function."""
    test_filter = filter_list.ObjectFilterList()

    with self.assertRaises(errors.WrongPlugin):
      test_filter.CompileFilter(
          u'SELECT stuff FROM machine WHERE conditions are met')

    with self.assertRaises(errors.WrongPlugin):
      test_filter.CompileFilter(
          u'/tmp/file_that_most_likely_does_not_exist')

    with self.assertRaises(errors.WrongPlugin):
      test_filter.CompileFilter(
          u'some random stuff that is destined to fail')

    with self.assertRaises(errors.WrongPlugin):
      test_filter.CompileFilter(
          u'some_stuff is "random" and other_stuff ')

    with self.assertRaises(errors.WrongPlugin):
      test_filter.CompileFilter(
          u'some_stuff is "random" and other_stuff is not "random"')

  def testFilterApprove(self):
    test_filter = filter_list.ObjectFilterList()

    one_rule = u'\n'.join([
        u'Again_Dude:',
        u'  description: Heavy artillery caught on fire',
        u'  case_nr: 62345',
        u'  analysts: [anonymous]',
        u'  urls: [cnn.com,microsoft.com]',
        u'  filter: message contains "dude where is my car"'])

    self._CreateFileAndTest(test_filter, one_rule)

    collection = u'\n'.join([
        u'Rule_Dude:',
        u'    description: This is the very case I talk about, a lot',
        u'    case_nr: 1235',
        u'    analysts: [dude, jack, horn]',
        u'    urls: [mbl.is,visir.is]',
        (u'    filter: date > "2012-01-01 10:54:13" and parser not contains '
         u'"evtx"'),
        u'',
        u'Again_Dude:',
        u'  description: Heavy artillery caught on fire',
        u'  case_nr: 62345',
        u'  analysts: [smith, perry, john]',
        u'  urls: [cnn.com,microsoft.com]',
        u'  filter: message contains "dude where is my car"',
        u'',
        u'Third_Rule_Of_Thumb:',
        u'    description: Another ticket for another day.',
        u'    case_nr: 234',
        u'    analysts: [joe]',
        u'    urls: [mbl.is,symantec.com/whereevillies,virustotal.com/myhash]',
        u'    filter: evil_bit is 1'])

    self._CreateFileAndTest(test_filter, collection)


if __name__ == '__main__':
  unittest.main()
