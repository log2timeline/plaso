# -*- coding: utf-8 -*-
"""This file contains the interface for analysis plugins."""

from __future__ import unicode_literals

import abc

from plaso.analysis import definitions
from plaso.analysis import logger
from plaso.containers import events


class AnalysisPlugin(object):
  """Class that defines the analysis plugin interface."""

  # The URLS should contain a list of URLs with additional information about
  # this analysis plugin.
  URLS = []

  # The name of the plugin. This is the name that is matched against when
  # loading plugins, so it is important that this name is short, concise and
  # explains the nature of the plugin easily. It also needs to be unique.
  NAME = 'analysis_plugin'

  def __init__(self):
    """Initializes an analysis plugin."""
    super(AnalysisPlugin, self).__init__()
    self.plugin_type = definitions.PLUGIN_TYPE_REPORT

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

  # pylint: disable=redundant-returns-doc
  @abc.abstractmethod
  def CompileReport(self, mediator):
    """Compiles a report of the analysis.

    After the plugin has received every copy of an event to
    analyze this function will be called so that the report
    can be assembled.

    Args:
      mediator (AnalysisMediator): mediates interactions between
          analysis plugins and other components, such as storage and dfvfs.

    Returns:
      AnalysisReport: report.
    """

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
