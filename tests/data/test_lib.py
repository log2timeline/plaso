# -*- coding: utf-8 -*-
"""Data files related functions and classes for testing."""

from __future__ import unicode_literals

from plaso.analysis import mediator as analysis_mediator
from plaso.analysis import tagging
from plaso.containers import sessions
from plaso.engine import knowledge_base
from plaso.storage.fake import writer as fake_writer

from tests import test_lib as shared_test_lib


class TaggingFileTestCase(shared_test_lib.BaseTestCase):
  """The unit test case for a tagging file."""

  _TAG_FILE = None

  def _CheckLabels(self, storage_writer, expected_labels):
    """Checks the labels of tagged events.

    Args:
      storage_writer (FakeStorageWriter): storage writer used for testing.
      expected_labels (list[str]): expected labels.
    """
    labels = []
    for event_tag in storage_writer.GetEventTags():
      labels.extend(event_tag.labels)

    labels = set(labels)
    expected_labels = set(expected_labels)

    self.assertEqual(len(labels), len(expected_labels))
    self.assertEqual(sorted(labels), sorted(expected_labels))

  def _TagEvent(self, event, event_data):
    """Tags an event.

    Args:
      event (Event): event.
      event_data (EventData): event data.

    Returns:
      FakeStorageWriter: storage writer.

    Raises:
      SkipTest: if the tag file does not exist.
    """
    tag_file_path = self._GetDataFilePath([self._TAG_FILE])
    self._SkipIfPathNotExists(tag_file_path)

    session = sessions.Session()

    storage_writer = fake_writer.FakeStorageWriter(session)
    storage_writer.Open()
    storage_writer.AddEventData(event_data)
    storage_writer.AddEvent(event)

    knowledge_base_object = knowledge_base.KnowledgeBase()

    mediator = analysis_mediator.AnalysisMediator(
        storage_writer, knowledge_base_object)

    plugin = tagging.TaggingAnalysisPlugin()
    plugin.SetAndLoadTagFile(tag_file_path)
    plugin.ExamineEvent(mediator, event, event_data)

    analysis_report = plugin.CompileReport(mediator)
    storage_writer.AddAnalysisReport(analysis_report)

    return storage_writer
