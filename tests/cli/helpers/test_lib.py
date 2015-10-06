# -*- coding: utf-8 -*-
"""CLI argument helper related functions and classes for testing."""

from plaso.lib import errors

from plaso.cli.helpers import interface


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
