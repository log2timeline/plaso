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


class AnalysisPlugin(object):
  """Class that defines the analysis plugin interface."""

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
  def CompileReport(self, analysis_mediator):
    """Compiles a report of the analysis.

    After the plugin has received every copy of an event to analyze this
    function will be called so that the report can be assembled.

    Args:
      analysis_mediator (AnalysisMediator): mediates interactions between
          analysis plugins and other components, such as storage and dfVFS.

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
  def ExamineEvent(
      self, analysis_mediator, event, event_data, event_data_stream):
    """Analyzes an event.

    Args:
      analysis_mediator (AnalysisMediator): mediates interactions between
          analysis plugins and other components, such as storage and dfVFS.
      event (EventObject): event.
      event_data (EventData): event data.
      event_data_stream (EventDataStream): event data stream.
    """
