# -*- coding: utf-8 -*-
"""Analysis plugin that labels events by session."""

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
    self._session_end_timestamp = None

  # pylint: disable=unused-argument
  def ExamineEvent(
      self, analysis_mediator, event, event_data, event_data_stream):
    """Analyzes an EventObject and tags it as part of a session.

    Args:
      analysis_mediator (AnalysisMediator): mediates interactions between
          analysis plugins and other components, such as storage and dfVFS.
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
    analysis_mediator.ProduceEventTag(event_tag)

    self._analysis_counter[label] += 1

  def SetMaximumPause(self, maximum_pause_minutes):
    """Sets the maximum pause interval between events to consider a session.

    Args:
      maximum_pause_minutes (int): maximum pause interval between events that
          are considered part of the same session, in minutes.
    """
    self._maximum_pause_microseconds = (
        maximum_pause_minutes * definitions.MICROSECONDS_PER_MINUTE)


manager.AnalysisPluginManager.RegisterPlugin(SessionizeAnalysisPlugin)
