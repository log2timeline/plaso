#!/usr/bin/python
# -*- coding: utf-8 -*-
"""CLI arguments helper related functions and classes for testing."""

from plaso.engine import knowledge_base
from plaso.formatters import mediator as formatters_mediator
from plaso.output import mediator as output_mediator

from tests.cli import test_lib as cli_test_lib


class OutputModuleArgumentsHelperTest(cli_test_lib.CLIToolTestCase):
  """Tests for an output module CLI arguments helper."""

  def _CreateOutputMediator(self):
    """Creates a test output mediator.

    Returns:
      OutputMediator: output mediator.
    """
    knowledge_base_object = knowledge_base.KnowledgeBase()
    formatter_mediator = formatters_mediator.FormatterMediator()
    return output_mediator.OutputMediator(
        knowledge_base_object, formatter_mediator)
