#!/usr/bin/python
# -*- coding: utf-8 -*-
"""CLI arguments helper related functions and classes for testing."""

from plaso.cli.helpers import interface
from plaso.engine import knowledge_base
from plaso.formatters import mediator as formatters_mediator
from plaso.lib import errors
from plaso.output import mediator as output_mediator

from tests.cli import test_lib as cli_test_lib


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
