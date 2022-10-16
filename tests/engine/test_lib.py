# -*- coding: utf-8 -*-
"""Engine related functions and classes for testing."""

from plaso.engine import knowledge_base
from plaso.storage.fake import writer as fake_writer

from tests import test_lib as shared_test_lib


class EngineTestCase(shared_test_lib.BaseTestCase):
  """Engine test case."""

  def _CreateKnowledgeBase(
      self, knowledge_base_values=None, time_zone_string='UTC'):
    """Creates a knowledge base.

    Args:
      knowledge_base_values (Optional[dict]): knowledge base values.
      time_zone_string (Optional[str]): time zone.

    Returns:
      KnowledgeBase: knowledge base.
    """
    knowledge_base_object = knowledge_base.KnowledgeBase()
    if knowledge_base_values:
      for identifier, value in knowledge_base_values.items():
        if identifier == 'codepage':
          knowledge_base_object.SetCodepage(value)
        else:
          knowledge_base_object.SetValue(identifier, value)

    if time_zone_string:
      knowledge_base_object.SetTimeZone(time_zone_string)

    return knowledge_base_object

  def _CreateStorageWriter(self):
    """Creates a storage writer object.

    Returns:
      FakeStorageWriter: storage writer.
    """
    storage_writer = fake_writer.FakeStorageWriter()
    storage_writer.Open()
    return storage_writer
