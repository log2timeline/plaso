#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""CLI arguments helper related functions and classes for testing."""

from __future__ import unicode_literals

from plaso.cli.helpers import interface
from plaso.engine import knowledge_base
from plaso.formatters import mediator as formatters_mediator
from plaso.lib import errors
from plaso.output import mediator as output_mediator

from tests.cli import test_lib as cli_test_lib


class TestHelper(interface.ArgumentsHelper):
  """Test CLI argument helper."""

  NAME = 'test_helper'
  DESCRIPTION = 'Test helper that does nothing.'

  @classmethod
  def AddArguments(cls, argument_group):
    """Adds command line arguments to an argument group.

    This function takes an argument parser or an argument group object and adds
    to it all the command line arguments this helper supports.

    Args:
      argument_group (argparse._ArgumentGroup|argparse.ArgumentParser):
          argparse group.
    """
    argument_group.add_argument(
        '-d', '--dynamic', action='store', default='', type=str,
        help='Stuff to insert into the arguments.', dest='dynamic')

  @classmethod
  def ParseOptions(cls, options, configuration_object):
    """Parses and validates options.

    Args:
      options (argparse.Namespace): parser options.
      configuration_object (object): object to be configured by the argument
          helper.

    Raises:
      BadConfigOption: when a configuration parameter fails validation.
    """
    if not getattr(options, 'dynamic', ''):
      raise errors.BadConfigOption('Always set this.')


class AnalysisPluginArgumentsHelperTest(cli_test_lib.CLIToolTestCase):
  """Tests an analysis plugin CLI arguments helper."""


class OutputModuleArgumentsHelperTest(cli_test_lib.CLIToolTestCase):
  """Tests an output module CLI arguments helper."""

  def _CreateOutputMediator(self):
    """Creates a test output mediator.

    Returns:
      OutputMediator: output mediator.
    """
    knowledge_base_object = knowledge_base.KnowledgeBase()
    formatter_mediator = formatters_mediator.FormatterMediator()
    return output_mediator.OutputMediator(
        knowledge_base_object, formatter_mediator)
