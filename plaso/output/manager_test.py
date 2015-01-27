#!/usr/bin/python
# -*- coding: utf-8 -*-
#
# Copyright 2015 The Plaso Project Authors.
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
"""Tests for the output manager."""

import unittest

from plaso.output import interface
from plaso.output import manager


class TestOutput(interface.LogOutputFormatter):
  """Test output module."""

  NAME = 'test_output'
  DESCRIPTION = u'This is a test output module.'

  def EventBody(self, event_object):
    """Writes the main body of an event to the output filehandle.

    Args:
      event_object: An event object (instance of EventObject).
    """
    pass


class OutputManagerTest(unittest.TestCase):
  """Tests for the output manager."""

  def testOutputRegistration(self):
    """Tests the RegisterOutput and DeregisterOutput functions."""
    # pylint: disable=protected-access
    number_of_parsers = len(manager.OutputManager._output_classes)

    manager.OutputManager.RegisterOutput(TestOutput)

    with self.assertRaises(KeyError):
      manager.OutputManager.RegisterOutput(TestOutput)

    self.assertEquals(
        len(manager.OutputManager._output_classes),
        number_of_parsers + 1)

    with self.assertRaises(KeyError):
      manager.OutputManager.RegisterOutput(TestOutput)

    manager.OutputManager.DeregisterOutput(TestOutput)
    self.assertEquals(
        len(manager.OutputManager._output_classes),
        number_of_parsers)

  def testGetOutputs(self):
    """Tests the GetOtputs function."""
    manager.OutputManager.RegisterOutput(TestOutput)

    names = []
    descriptions = []

    for name, description in manager.OutputManager.GetOutputs():
      names.append(name)
      descriptions.append(description)

    self.assertIn('test_output', names)
    self.assertIn(u'This is a test output module.', descriptions)
    manager.OutputManager.DeregisterOutput(TestOutput)


if __name__ == '__main__':
  unittest.main()
