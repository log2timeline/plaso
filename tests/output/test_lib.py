# -*- coding: utf-8 -*-
"""Output related functions and classes for testing."""

from plaso.engine import knowledge_base
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

    output_mediator = mediator.OutputMediator(
        knowledge_base_object, data_location=shared_test_lib.TEST_DATA_PATH)

    return output_mediator
