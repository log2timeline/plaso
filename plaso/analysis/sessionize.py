# -*- coding: utf-8 -*-
"""A plugin to tag events according to rules in a tag file."""

from __future__ import unicode_literals

from plaso.analysis import interface
from plaso.analysis import manager
from plaso.containers import reports
from plaso.lib import definitions


class SessionizeAnalysisPlugin(interface.AnalysisPlugin):
  """Analysis plugin that labels events by session."""

  NAME = 'sessionize'

  ENABLE_IN_EXTRACTION = False

  _EVENT_TAG_COMMENT = 'Tag applied by sessionize analysis plugin.'

  _DEFAULT_MAXIMUM_PAUSE = 10 * definitions.MICROSECONDS_PER_MINUTE

  def __init__(self):
    """Initializes a sessionize analysis plugin."""
    super(SessionizeAnalysisPlugin, self).__init__()
    self._maximum_pause_microseconds = self._DEFAULT_MAXIMUM_PAUSE
    self._session_counter = 0
    self._events_per_session = []
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
          analysis plugins and other components, such as storage and dfvfs.

    Returns:
      AnalysisReport: analysis report.
    """
    report_text = [
        'Sessionize plugin identified {0:d} sessions and '
        'applied {1:d} tags.'.format(
            len(self._events_per_session), self._number_of_event_tags)]
    for session, event_count in enumerate(self._events_per_session):
      report_text.append('\tSession {0:d}: {1:d} events'.format(
          session, event_count))
    report_text = '\n'.join(report_text)
    return reports.AnalysisReport(plugin_name=self.NAME, text=report_text)

  # pylint: disable=unused-argument
  def ExamineEvent(self, mediator, event, event_data):
    """Analyzes an EventObject and tags it as part of a session.

    Args:
      mediator (AnalysisMediator): mediates interactions between analysis
          plugins and other components, such as storage and dfvfs.
      event (EventObject): event to examine.
      event_data (EventData): event data.
    """
    if self._session_end_timestamp is None:
      self._session_end_timestamp = (
          event.timestamp + self._maximum_pause_microseconds)
      self._events_per_session.append(0)

    if event.timestamp > self._session_end_timestamp:
      self._session_counter += 1
      self._events_per_session.append(0)

    self._session_end_timestamp = (
        event.timestamp + self._maximum_pause_microseconds)
    # The counter for the current session is the always the last item in
    # the list.
    self._events_per_session[-1] += 1

    label = 'session_{0:d}'.format(self._session_counter)
    event_tag = self._CreateEventTag(event, self._EVENT_TAG_COMMENT, [label])
    mediator.ProduceEventTag(event_tag)
    self._number_of_event_tags += 1


manager.AnalysisPluginManager.RegisterPlugin(SessionizeAnalysisPlugin)
