# -*- coding: utf-8 -*-
"""Data files related functions and classes for testing."""

from plaso.analysis import mediator as analysis_mediator
from plaso.analysis import tagging
from plaso.containers import events
from plaso.lib import definitions
from plaso.storage.fake import writer as fake_writer

from tests import test_lib as shared_test_lib


class TaggingFileTestCase(shared_test_lib.BaseTestCase):
  """The unit test case for a tagging file."""

  _TAG_FILE = None

  _TEST_TIMESTAMP = shared_test_lib.CopyTimestampFromString(
      '2020-04-04 14:56:39')

  def _CheckLabels(self, storage_writer, expected_labels):
    """Checks the labels of tagged events.

    Args:
      storage_writer (FakeStorageWriter): storage writer used for testing.
      expected_labels (list[str]): expected labels.
    """
    labels = []
    for event_tag in storage_writer.GetAttributeContainers(
        events.EventTag.CONTAINER_TYPE):
      labels.extend(event_tag.labels)

    labels = set(labels)
    expected_labels = set(expected_labels)

    self.assertEqual(len(labels), len(expected_labels))
    self.assertEqual(sorted(labels), sorted(expected_labels))

  def _CheckTaggingRule(
      self, event_data_class, attribute_values_per_name, expected_rule_names):
    """Tests a tagging rule.

    Args:
      event_data_class (type): class of the event data object to use in tests.
      attribute_values_per_name (dict[str, list[str]): values of the event data
          attribute values per name, to use for testing events that match the
          tagging rule.
      expected_rule_names (list[str]): expected rule names.
    """
    event = events.EventObject()
    event.timestamp = self._TEST_TIMESTAMP
    event.timestamp_desc = definitions.TIME_DESCRIPTION_UNKNOWN

    if not attribute_values_per_name:
      event_data = event_data_class()
      storage_writer = self._TagEvent(event, event_data, None)

      self._CheckLabels(storage_writer, expected_rule_names)

    else:
      maximum_number_of_attribute_values = max(
          len(attribute_values)
          for attribute_values in attribute_values_per_name.values())

      # Test if variations defined by the attribute_values_per_name match
      # the tagging rule.
      for test_index in range(maximum_number_of_attribute_values):
        # Create the test event data and set the attributes to one of
        # the test values.
        event_data = event_data_class()
        for attribute_name, attribute_values in (
            attribute_values_per_name.items()):
          attribute_value_index = min(test_index, len(attribute_values) - 1)
          attribute_value = attribute_values[attribute_value_index]
          setattr(event_data, attribute_name, attribute_value)

        storage_writer = self._TagEvent(event, event_data, None)

        self._CheckLabels(storage_writer, expected_rule_names)

      # Test if bogus variations on attribute_values_per_name do not match
      # the tagging rule.
      for test_attribute_name in attribute_values_per_name.keys():
        # Create the test event data and set the attributes to one of
        # the test values.
        event_data = event_data_class()
        for attribute_name, attribute_values in (
            attribute_values_per_name.items()):
          if attribute_name == test_attribute_name:
            attribute_value = 'BOGUS'
          else:
            attribute_value = attribute_values[0]
          setattr(event_data, attribute_name, attribute_value)

        storage_writer = self._TagEvent(event, event_data, None)

        self._CheckLabels(storage_writer, [])

  def _TagEvent(self, event, event_data, event_data_stream):
    """Tags an event.

    Args:
      event (Event): event.
      event_data (EventData): event data.
      event_data_stream (EventDataStream): event data stream.

    Returns:
      FakeStorageWriter: storage writer.

    Raises:
      SkipTest: if the tag file does not exist.
    """
    tag_file_path = self._GetDataFilePath([self._TAG_FILE])
    self._SkipIfPathNotExists(tag_file_path)

    storage_writer = fake_writer.FakeStorageWriter()
    storage_writer.Open()

    if event_data_stream:
      storage_writer.AddAttributeContainer(event_data_stream)
      event_data_stream_identifier = event_data_stream.GetIdentifier()
      event_data.SetEventDataStreamIdentifier(event_data_stream_identifier)

    storage_writer.AddAttributeContainer(event_data)
    event_data_identifier = event_data.GetIdentifier()
    event.SetEventDataIdentifier(event_data_identifier)

    storage_writer.AddAttributeContainer(event)

    mediator = analysis_mediator.AnalysisMediator()
    mediator.SetStorageWriter(storage_writer)

    plugin = tagging.TaggingAnalysisPlugin()
    plugin.SetAndLoadTagFile(tag_file_path)
    plugin.ExamineEvent(mediator, event, event_data, event_data_stream)

    analysis_report = plugin.CompileReport(mediator)
    storage_writer.AddAttributeContainer(analysis_report)

    return storage_writer
