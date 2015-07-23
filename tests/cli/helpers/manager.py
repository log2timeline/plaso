#!/usr/bin/python
# -*- coding: utf-8 -*-
"""Tests for the CLI argument helper manager."""

import argparse
import unittest

from plaso.lib import errors

from plaso.cli.helpers import interface
from plaso.cli.helpers import manager


class TestHelper(interface.ArgumentsHelper):
  """Test CLI argument helper."""

  NAME = 'test_helper'
  DESCRIPTION = u'Test helper that does nothing.'

  @classmethod
  def AddArguments(cls, argument_group):
    """Add command line arguments to an argument group."""
    argument_group.add_argument(
        u'-d', u'--dynamic', action='store', default=u'', type=str,
        help=u'Stuff to insert into the arguments.', dest=u'dynamic')

  @classmethod
  def ParseOptions(cls, options, unused_config_object):
    """Parse and validate the configuration options."""
    if not getattr(options, 'dynamic', u''):
      raise errors.BadConfigOption(u'Always set this.')


class AnotherTestHelper(interface.ArgumentsHelper):
  """Another test CLI argument helper."""

  NAME = 'another_test_helper'
  DESCRIPTION = u'Another test helper that does nothing.'

  @classmethod
  def AddArguments(cls, argument_group):
    """Add command line arguments to an argument group."""
    argument_group.add_argument(
        u'-c', u'--correcto', dest=u'correcto', action='store_true',
        default=False, help=u'The correcto option.')

  @classmethod
  def ParseOptions(cls, options, unused_config_object):
    """Parse and validate the configurational options."""
    if not hasattr(options, 'correcto'):
      raise errors.BadConfigOption(u'Correcto not set.')

    if not isinstance(getattr(options, u'correcto', None), bool):
      raise errors.BadConfigOption(u'Correcto wrongly formatted.')


class HelperManagerTest(unittest.TestCase):
  """Tests for the parsers manager."""

  def testHelperRegistration(self):
    """Tests the RegisterHelper and DeregisterHelper functions."""
    # pylint: disable=protected-access
    number_of_helpers = len(manager.ArgumentHelperManager._helper_classes)

    manager.ArgumentHelperManager.RegisterHelper(TestHelper)
    self.assertEqual(
        len(manager.ArgumentHelperManager._helper_classes),
        number_of_helpers + 1)

    with self.assertRaises(KeyError):
      manager.ArgumentHelperManager.RegisterHelper(TestHelper)

    manager.ArgumentHelperManager.DeregisterHelper(TestHelper)
    self.assertEqual(
        len(manager.ArgumentHelperManager._helper_classes),
        number_of_helpers)

  def testGetHelperNames(self):
    """Tests the GetHelperNames function."""
    manager.ArgumentHelperManager.RegisterHelper(TestHelper)
    self.assertIn(
        TestHelper.NAME, manager.ArgumentHelperManager.GetHelperNames())
    manager.ArgumentHelperManager.DeregisterHelper(TestHelper)

  def testCommandLineArguments(self):
    """Test the AddCommandLineArguments and function."""
    manager.ArgumentHelperManager.RegisterHelpers(
        [TestHelper, AnotherTestHelper])

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

    manager.ArgumentHelperManager.DeregisterHelper(TestHelper)
    manager.ArgumentHelperManager.DeregisterHelper(AnotherTestHelper)


if __name__ == '__main__':
  unittest.main()
