#!/usr/bin/python
# -*- coding: utf-8 -*-
"""Tests for the CLI argument helper manager."""

from __future__ import unicode_literals

import argparse
import unittest

from plaso.cli.helpers import interface
from plaso.cli.helpers import manager
from plaso.lib import errors

from tests.cli.helpers import test_lib


class AnotherTestHelper(interface.ArgumentsHelper):
  """Another test CLI argument helper."""

  NAME = 'another_test_helper'
  DESCRIPTION = 'Another test helper that does nothing.'

  @classmethod
  def AddArguments(cls, argument_group):
    """Add command line arguments to an argument group."""
    argument_group.add_argument(
        '-c', '--correcto', dest='correcto', action='store_true',
        default=False, help='The correcto option.')

  @classmethod
  def ParseOptions(cls, options, unused_config_object):
    """Parse and validate the configurational options."""
    if not hasattr(options, 'correcto'):
      raise errors.BadConfigOption('Correcto not set.')

    if not isinstance(getattr(options, 'correcto', None), bool):
      raise errors.BadConfigOption('Correcto wrongly formatted.')


class HelperManagerTest(unittest.TestCase):
  """Tests the parsers manager."""

  # pylint: disable=protected-access

  def testHelperRegistration(self):
    """Tests the RegisterHelper and DeregisterHelper functions."""
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

  def testCommandLineArguments(self):
    """Test the AddCommandLineArguments and function."""
    manager.ArgumentHelperManager.RegisterHelpers([
        test_lib.TestHelper, AnotherTestHelper])

    arg_parser = argparse.ArgumentParser(conflict_handler='resolve')
    manager.ArgumentHelperManager.AddCommandLineArguments(arg_parser)

    # Assert the parameters have been set.
    options = arg_parser.parse_args([])

    self.assertTrue(hasattr(options, 'dynamic'))
    self.assertTrue(hasattr(options, 'correcto'))

    self.assertFalse(hasattr(options, 'foobar'))

    # Make the parameters fail validation.
    options.correcto = 'sfd'
    with self.assertRaises(errors.BadConfigOption):
      manager.ArgumentHelperManager.ParseOptions(options, None)

    options.correcto = True
    options.dynamic = 'now stuff'
    manager.ArgumentHelperManager.ParseOptions(options, None)

    manager.ArgumentHelperManager.DeregisterHelper(test_lib.TestHelper)
    manager.ArgumentHelperManager.DeregisterHelper(AnotherTestHelper)


if __name__ == '__main__':
  unittest.main()
