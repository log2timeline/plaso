# -*- coding: utf-8 -*-
"""Output related functions and classes for testing."""

from __future__ import unicode_literals

from plaso.engine import knowledge_base
from plaso.formatters import mediator as formatters_mediator
from plaso.output import mediator

from tests import test_lib as shared_test_lib


class TestConfig(object):
  """Test configuration."""


class OutputModuleTestCase(shared_test_lib.BaseTestCase):
  """The unit test case for a output module."""

  def _CreateOutputMediator(self, storage_file=None):
    """Creates a test output mediator.

    Args:
      storage_file (Optional[StorageFile]): storage file.

    Returns:
      OutputMediator: output mediator.
    """
    knowledge_base_object = knowledge_base.KnowledgeBase()

    if storage_file:
      # TODO: clean up
      for session in storage_file.GetSessions():
        if not session.source_configurations:
          storage_file.ReadSystemConfiguration(knowledge_base_object)
        else:
          for source_configuration in session.source_configurations:
            knowledge_base_object.ReadSystemConfigurationArtifact(
                source_configuration.system_configuration,
                session_identifier=session.identifier)

    formatter_mediator = formatters_mediator.FormatterMediator()
    output_mediator = mediator.OutputMediator(
        knowledge_base_object, formatter_mediator)

    return output_mediator
