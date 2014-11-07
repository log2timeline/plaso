#!/usr/bin/python
# -*- coding: utf-8 -*-
# Copyright 2013 The Plaso Project Authors.
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
"""This file contains the unit tests for the utils library of methods."""
import unittest

from plaso.lib import utils


class UtilsTestCase(unittest.TestCase):
  """The unit test for utils method collection."""

  def testIsText(self):
    """Test the IsText method."""
    bytes_in = 'this is My Weird ASCII and non whatever string.'
    self.assertTrue(utils.IsText(bytes_in))

    bytes_in = u'Plaso Síar Og Raðar Þessu'
    self.assertTrue(utils.IsText(bytes_in))

    bytes_in = '\x01\62LSO\xFF'
    self.assertFalse(utils.IsText(bytes_in))

    bytes_in = 'T\x00h\x00i\x00s\x00\x20\x00'
    self.assertTrue(utils.IsText(bytes_in))

    bytes_in = 'Ascii\x00'
    self.assertTrue(utils.IsText(bytes_in))

    bytes_in = 'Ascii Start then...\x00\x99\x23'
    self.assertFalse(utils.IsText(bytes_in))


if __name__ == '__main__':
  unittest.main()
