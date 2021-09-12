# -*- coding: utf-8 -*-
"""A plugin to tag events according to rules in a tag file."""

from plaso.analysis import interface
from plaso.analysis import manager
from plaso.lib import definitions


class SessionizeAnalysisPlugin(interface.AnalysisPlugin):
  """Analysis plugin that labels events by session."""

  NAME = 'sessionize'

  _DEFAULT_MAXIMUM_PAUSE = 10 * definitions.MICROSECONDS_PER_MINUTE

  def __init__(self):
    """Initializes a sessionize analysis plugin."""
    super(SessionizeAnalysisPlugin, self).__init__()
    self._current_session_number = 0
    self._maximum_pause_microseconds = self._DEFAULT_MAXIMUM_PAUSE
    self._number_of_event_tags = 0
    self._session_end_timestamp = None

  def SetMaximumPause(self, maximum_pause_minutes):
    """Sets the maximum pause interval between events to consider a session.

    Args:
      maximum_pause_minutes (int): maximum gap between events that are part of
          the same session, in minutes.
    """
    self._maximum_pause_microseconds = (
        maximum_pause_minutes * definitions.MICROSECONDS_PER_MINUTE)

  def CompileReport(self, mediator):
    """Compiles an analysis report.

    Args:
      mediator (AnalysisMediator): mediates interactions between
          analysis plugins and other components, such as storage and dfVFS.

    Returns:
      AnalysisReport: analysis report.
    """
    report_text = [
        'Sessionize plugin identified {0:d} sessions and created '
        '{1:d} event tags.'.format(
            self._current_session_number + 1, self._number_of_event_tags)]

    analysis_report = super(SessionizeAnalysisPlugin, self).CompileReport(
        mediator)
    analysis_report.text = report_text
    return analysis_report

  # pylint: disable=unused-argument
  def ExamineEvent(self, mediator, event, event_data, event_data_stream):
    """Analyzes an EventObject and tags it as part of a session.

    Args:
      mediator (AnalysisMediator): mediates interactions between analysis
          plugins and other components, such as storage and dfVFS.
      event (EventObject): event to examine.
      event_data (EventData): event data.
      event_data_stream (EventDataStream): event data stream.
    """
    if (self._session_end_timestamp is not None and
        event.timestamp > self._session_end_timestamp):
      self._current_session_number += 1

    self._session_end_timestamp = (
        event.timestamp + self._maximum_pause_microseconds)

    label = 'session_{0:d}'.format(self._current_session_number)

    event_tag = self._CreateEventTag(event, [label])
    mediator.ProduceEventTag(event_tag)

    self._analysis_counter[label] += 1
    self._number_of_event_tags += 1


manager.AnalysisPluginManager.RegisterPlugin(SessionizeAnalysisPlugin)
