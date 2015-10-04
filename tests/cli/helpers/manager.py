#!/usr/bin/python
# -*- coding: utf-8 -*-
"""Tests for the CLI argument helper manager."""

import argparse
import unittest

from plaso.lib import errors

from plaso.cli.helpers import manager

from tests.cli.helpers import test_lib


class HelperManagerTest(unittest.TestCase):
  """Tests for the parsers manager."""

  def testHelperRegistration(self):
    """Tests the RegisterHelper and DeregisterHelper functions."""
    # pylint: disable=protected-access
    number_of_helpers = len(manager.ArgumentHelperManager._helper_classes)

    manager.ArgumentHelperManager.RegisterHelper(test_lib.TestHelper)
    self.assertEqual(
        len(manager.ArgumentHelperManager._helper_classes),
        number_of_helpers + 1)

    with self.assertRaises(KeyError):
      manager.ArgumentHelperManager.RegisterHelper(test_lib.TestHelper)

    manager.ArgumentHelperManager.DeregisterHelper(test_lib.TestHelper)
    self.assertEqual(
        len(manager.ArgumentHelperManager._helper_classes),
        number_of_helpers)

  def testGetHelperNames(self):
    """Tests the GetHelperNames function."""
    manager.ArgumentHelperManager.RegisterHelper(test_lib.TestHelper)
    self.assertIn(
        test_lib.TestHelper.NAME,
        manager.ArgumentHelperManager.GetHelperNames())
    manager.ArgumentHelperManager.DeregisterHelper(test_lib.TestHelper)

  def testCommandLineArguments(self):
    """Test the AddCommandLineArguments and function."""
    manager.ArgumentHelperManager.RegisterHelpers([
        test_lib.TestHelper, test_lib.AnotherTestHelper])

    arg_parser = argparse.ArgumentParser(conflict_handler=u'resolve')
    manager.ArgumentHelperManager.AddCommandLineArguments(arg_parser)

    # Assert the parameters have been set.
    options = arg_parser.parse_args([])

    self.assertTrue(hasattr(options, u'dynamic'))
    self.assertTrue(hasattr(options, u'correcto'))

    self.assertFalse(hasattr(options, u'foobar'))

    # Make the parameters fail validation.
    options.correcto = 'sfd'
    with self.assertRaises(errors.BadConfigOption):
      manager.ArgumentHelperManager.ParseOptions(options, None)

    options.correcto = True
    options.dynamic = 'now stuff'
    manager.ArgumentHelperManager.ParseOptions(options, None)

    manager.ArgumentHelperManager.DeregisterHelper(test_lib.TestHelper)
    manager.ArgumentHelperManager.DeregisterHelper(test_lib.AnotherTestHelper)


if __name__ == '__main__':
  unittest.main()
