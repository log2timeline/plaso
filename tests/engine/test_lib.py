# -*- coding: utf-8 -*-
"""Engine related functions and classes for testing."""

from plaso.storage.fake import writer as fake_writer

from tests import test_lib as shared_test_lib


class EngineTestCase(shared_test_lib.BaseTestCase):
  """Engine test case."""

  def _CreateStorageWriter(self):
    """Creates a storage writer object.

    Returns:
      FakeStorageWriter: storage writer.
    """
    storage_writer = fake_writer.FakeStorageWriter()
    storage_writer.Open()
    return storage_writer
