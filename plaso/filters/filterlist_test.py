#!/usr/bin/python
# -*- coding: utf-8 -*-
"""Tests for the PFilters filter."""

import os
import logging
import tempfile
import unittest

from plaso.filters import filterlist
from plaso.filters import test_helper


class ObjectFilterTest(test_helper.FilterTestHelper):
  """Tests for the ObjectFilterList filter."""

  def setUp(self):
    """Sets up the needed objects used throughout the test."""
    self.test_filter = filterlist.ObjectFilterList()

  def testFilterFail(self):
    """Run few tests that should not be a proper filter."""
    self.TestFail('SELECT stuff FROM machine WHERE conditions are met')
    self.TestFail('/tmp/file_that_most_likely_does_not_exist')
    self.TestFail('some random stuff that is destined to fail')
    self.TestFail('some_stuff is "random" and other_stuff ')
    self.TestFail('some_stuff is "random" and other_stuff is not "random"')

  def CreateFileAndTest(self, content):
    """Creates a file and then runs the test."""
    name = ''
    with tempfile.NamedTemporaryFile(delete=False) as file_object:
      name = file_object.name
      file_object.write(content)

    self.TestTrue(name)

    try:
      os.remove(name)
    except (OSError, IOError) as exception:
      logging.warning(
          u'Unable to remove temporary file: {0:s} with error: {1:s}'.format(
              name, exception))

  def testFilterApprove(self):
    one_rule = u'\n'.join([
        u'Again_Dude:',
        u'  description: Heavy artillery caught on fire',
        u'  case_nr: 62345',
        u'  analysts: [anonymous]',
        u'  urls: [cnn.com,microsoft.com]',
        u'  filter: message contains "dude where is my car"'])

    self.CreateFileAndTest(one_rule)

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

    self.CreateFileAndTest(collection)


if __name__ == '__main__':
  unittest.main()
