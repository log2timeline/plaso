# -*- coding: utf-8 -*-
"""This file contains the interface for analysis plugins."""

import abc
import calendar
import collections
import time

from plaso.analysis import definitions as analysis_definitions
from plaso.analysis import logger
from plaso.containers import events
from plaso.containers import reports
from plaso.lib import definitions
from plaso.storage import event_tag_index


class AnalysisPlugin(object):
  """Class that defines the analysis plugin interface.

  Attributes:
    number_of_consumed_events (int): number of events consumed by the analysis
        plugin.
    number_of_filtered_events (int): number of events filtered by the event
        filter during analysis.
    plugin_type (str): analysis plugin type.
  """

  # The name of the plugin. This is the name that is matched against when
  # loading plugins, so it is important that this name is short, concise and
  # explains the nature of the plugin easily. It also needs to be unique.
  NAME = 'analysis_plugin'

  # Flag to indicate the analysis is for testing purposes only.
  TEST_PLUGIN = False

  def __init__(self):
    """Initializes an analysis plugin."""
    super(AnalysisPlugin, self).__init__()
    self._analysis_counter = collections.Counter()
    self._event_tag_index = event_tag_index.EventTagIndex()

    self.number_of_consumed_events = 0
    self.number_of_filtered_events = 0
    self.plugin_type = analysis_definitions.PLUGIN_TYPE_REPORT

  @property
  def plugin_name(self):
    """str: name of the plugin."""
    return self.NAME

  def _CreateEventTag(self, event, labels):
    """Creates an event tag.

    Args:
      event (EventObject): event to tag.
      labels (list[str]): event tag labels.

    Returns:
      EventTag: the event tag.
    """
    event_identifier = event.GetIdentifier()

    event_tag = events.EventTag()
    event_tag.SetEventIdentifier(event_identifier)
    event_tag.AddLabels(labels)

    event_identifier_string = event_identifier.CopyToString()
    logger.debug('Tagged event: {0:s} with labels: {1:s}'.format(
        event_identifier_string, ', '.join(labels)))

    return event_tag

  # pylint: disable=unused-argument
  def CompileReport(self, mediator):
    """Compiles a report of the analysis.

    After the plugin has received every copy of an event to analyze this
    function will be called so that the report can be assembled.

    Args:
      mediator (AnalysisMediator): mediates interactions between
          analysis plugins and other components, such as storage and dfvfs.

    Returns:
      AnalysisReport: report.
    """
    analysis_report = reports.AnalysisReport(plugin_name=self.NAME)

    time_elements = time.gmtime()
    time_compiled = calendar.timegm(time_elements)
    analysis_report.time_compiled = (
        time_compiled * definitions.MICROSECONDS_PER_SECOND)

    analysis_report.analysis_counter = self._analysis_counter

    return analysis_report

  @abc.abstractmethod
  def ExamineEvent(self, mediator, event, event_data, event_data_stream):
    """Analyzes an event.

    Args:
      mediator (AnalysisMediator): mediates interactions between
          analysis plugins and other components, such as storage and dfvfs.
      event (EventObject): event.
      event_data (EventData): event data.
      event_data_stream (EventDataStream): event data stream.
    """

  def ProcessEventStore(self, mediator, storage_reader, event_filter=None):
    """Analyzes an event store.

    Args:
      mediator (AnalysisMediator): mediates interactions between
          analysis plugins and other components, such as storage and dfvfs.
      storage_reader (StorageReader): storage reader.
      event_filter (Optional[EventObjectFilter]): event filter.
    """
    # TODO: determine if filter_limit makes sense for analysis plugins or
    # that it should be removed.
    filter_limit = getattr(event_filter, 'limit', None)

    # TODO: test if GetEvents is faster for analysis plugins that do not
    # require the events to be in chronological order.
    # if event_filter:
    #   event_generator = storage_reader.GetSortedEvents()
    # else:
    #   event_generator = storage_reader.GetEvents()

    for event in storage_reader.GetSortedEvents():
      if mediator.abort:
        break

      event_data_identifier = event.GetEventDataIdentifier()
      event_data = storage_reader.GetEventDataByIdentifier(
          event_data_identifier)

      event_data_stream_identifier = event_data.GetEventDataStreamIdentifier()
      event_data_stream = None
      if event_data_stream_identifier:
        event_data_stream = storage_reader.GetEventDataStreamByIdentifier(
            event_data_stream_identifier)

      event_identifier = event.GetIdentifier()
      event_tag = self._event_tag_index.GetEventTagByIdentifier(
          storage_reader, event_identifier)

      filter_match = None
      if event_filter:
        filter_match = event_filter.Match(
            event, event_data, event_data_stream, event_tag)

        # pylint: disable=singleton-comparison
        if filter_match == False:
          self.number_of_filtered_events += 1
          continue

      self.ExamineEvent(mediator, event, event_data, event_data_stream)
      self.number_of_consumed_events += 1

      if filter_limit and filter_limit == self.number_of_consumed_events:
        break
