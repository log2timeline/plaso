#!/usr/bin/python
# -*- coding: utf-8 -*-
#
# Copyright 2014 The Plaso Project Authors.
# Please see the AUTHORS file for details on individual authors.
#
# Licensed under the Apache License, Version 2.0 (the "License");
# you may not use this file except in compliance with the License.
# You may obtain a copy of the License at
#
#    http://www.apache.org/licenses/LICENSE-2.0
#
# Unless required by applicable law or agreed to in writing, software
# distributed under the License is distributed on an "AS IS" BASIS,
# WITHOUT WARRANTIES OR CONDITIONS OF ANY KIND, either express or implied.
# See the License for the specific language governing permissions and
# limitations under the License.
"""Tests for the preg front-end."""

import StringIO
import unittest

from plaso.frontend import preg
from plaso.frontend import test_lib


class StringIOOutputWriter(object):
  """Class that implements a StringIO output writer."""

  def __init__(self):
    super(StringIOOutputWriter, self).__init__()
    self._string_obj = StringIO.StringIO()

  def Write(self, string):
    """Writes a string to the StringIO object."""
    self._string_obj.write(string)

  def GetValue(self):
    """Returns the write buffer from the output writer."""
    return self._string_obj.getvalue()


class PregFrontendTest(test_lib.FrontendTestCase):
  """Tests for the preg front-end."""

  def testRunPlugin(self):
    """Tests running the preg frontend against a plugin."""
    output_writer = StringIOOutputWriter()
    test_front_end = preg.PregFrontend(output_writer)

    options = test_lib.Options()
    options.regfile = self._GetTestFilePath(['NTUSER.DAT'])
    options.verbose = False

    test_front_end.ParseOptions(options, source_option='image')
    test_front_end.RunModeRegistryPlugin(options, u'userassist')

    self.assertTrue((
        u'UEME_RUNPATH:C:\\Program Files\\Internet Explorer\\iexplore.exe : '
        u'[Count: 1]') in output_writer.GetValue())

    # TODO: Add tests that parse a disk image. Test both Registry key parsing
    # and plugin parsing.

  def testRunAgainstKey(self):
    """Tests running the preg frontend against a Registry key."""
    output_writer = StringIOOutputWriter()
    test_front_end = preg.PregFrontend(output_writer)

    options = test_lib.Options()
    options.key = u'\\Microsoft\\Windows NT\\CurrentVersion'
    options.regfile = self._GetTestFilePath(['SOFTWARE'])
    options.verbose = False

    test_front_end.ParseOptions(options, source_option='image')
    test_front_end.RunModeRegistryKey(options, u'')

    self.assertTrue(
        u'Product name : Windows 7 Ultimate' in output_writer.GetValue())
    # TODO: Add tests for running in console mode.


if __name__ == '__main__':
  unittest.main()
