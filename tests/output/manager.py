#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""Tests for the output manager."""

import unittest

from plaso.output import interface
from plaso.output import manager


class TestOutput(interface.OutputModule):
  """Test output module."""

  NAME = 'test_output'
  DESCRIPTION = 'This is a test output module.'

  # pylint: disable=unused-argument

  def _GetFieldValues(
      self, output_mediator, event, event_data, event_data_stream, event_tag):
    """Retrieves the output field values.

    Args:
      output_mediator (OutputMediator): mediates interactions between output
          modules and other components, such as storage and dfVFS.
      event (EventObject): event.
      event_data (EventData): event data.
      event_data_stream (EventDataStream): event data stream.
      event_tag (EventTag): event tag.

    Returns:
      dict[str, str]: output field values per name.
    """
    return {}

  def _WriteFieldValues(self, output_mediator, field_values):
    """Writes field values to the output.

    Args:
      output_mediator (OutputMediator): mediates interactions between output
          modules and other components, such as storage and dfVFS.
      field_values (dict[str, str]): output field values per name.
    """
    return


class OutputManagerTest(unittest.TestCase):
  """Tests for the output manager."""

  def testRegistration(self):
    """Tests the RegisterOutput and DeregisterOutput functions."""
    # pylint: disable=protected-access
    number_of_parsers = len(manager.OutputManager._output_classes)

    manager.OutputManager.RegisterOutput(TestOutput)

    with self.assertRaises(KeyError):
      manager.OutputManager.RegisterOutput(TestOutput)

    self.assertEqual(
        len(manager.OutputManager._output_classes),
        number_of_parsers + 1)

    with self.assertRaises(KeyError):
      manager.OutputManager.RegisterOutput(TestOutput)

    manager.OutputManager.DeregisterOutput(TestOutput)
    self.assertEqual(
        len(manager.OutputManager._output_classes),
        number_of_parsers)

  def testGetOutputClass(self):
    """Tests the GetOutputClass function."""
    manager.OutputManager.RegisterOutput(TestOutput)

    output_class = manager.OutputManager.GetOutputClass('test_output')
    self.assertEqual(output_class, TestOutput)

    with self.assertRaises(ValueError):
      _ = manager.OutputManager.GetOutputClass(1)

    with self.assertRaises(KeyError):
      _ = manager.OutputManager.GetOutputClass('bogus')

    manager.OutputManager.DeregisterOutput(TestOutput)

  def testGetDisabledOutputClasses(self):
    """Tests the GetDisabledOutputClasses function."""
    manager.OutputManager.RegisterOutput(TestOutput, disabled=True)

    names = []
    output_classes = []

    for name, output_class in manager.OutputManager.GetDisabledOutputClasses():
      names.append(name)
      output_classes.append(output_class)

    self.assertIn('test_output', names)
    self.assertIn(TestOutput, output_classes)

    manager.OutputManager.DeregisterOutput(TestOutput)

  def testGetOutputClasses(self):
    """Tests the GetOutputClasses function."""
    manager.OutputManager.RegisterOutput(TestOutput)

    names = []
    output_classes = []

    for name, output_class in manager.OutputManager.GetOutputClasses():
      names.append(name)
      output_classes.append(output_class)

    self.assertIn('test_output', names)
    self.assertIn(TestOutput, output_classes)

    manager.OutputManager.DeregisterOutput(TestOutput)

  def testHasOutputClass(self):
    """Tests the HasOutputClass function."""
    manager.OutputManager.RegisterOutput(TestOutput)

    self.assertTrue(manager.OutputManager.HasOutputClass('test_output'))
    self.assertFalse(manager.OutputManager.HasOutputClass('bogus'))
    self.assertFalse(manager.OutputManager.HasOutputClass(1))

    manager.OutputManager.DeregisterOutput(TestOutput)

  def testNewOutputModule(self):
    """Tests the NewOutputModule function."""
    manager.OutputManager.RegisterOutput(TestOutput)

    output_module = manager.OutputManager.NewOutputModule('test_output')
    self.assertIsInstance(output_module, TestOutput)

    with self.assertRaises(ValueError):
      manager.OutputManager.NewOutputModule(1)

    with self.assertRaises(KeyError):
      manager.OutputManager.NewOutputModule('bogus')

    manager.OutputManager.DeregisterOutput(TestOutput)


if __name__ == '__main__':
  unittest.main()
