# -*- coding: utf-8 -*-
"""Analysis plugin for testing exceeding memory consumption."""

from __future__ import unicode_literals

from plaso.analysis import interface
from plaso.analysis import manager
from plaso.containers import reports


class TestMemoryAnalysisPlugin(interface.AnalysisPlugin):
  """Analysis plugin for testing memory consumption."""

  NAME = 'test_memory'

  TEST_PLUGIN = True

  def __init__(self):
    """Initializes an analysis plugin for testing memory consumption."""
    super(TestMemoryAnalysisPlugin, self).__init__()
    self._objects = []

  def CompileReport(self, analysis_mediator):
    """Compiles an analysis report.

    Args:
      analysis_mediator (AnalysisMediator): mediates interactions between
          analysis plugins and other components, such as storage and dfVFS.

    Returns:
      AnalysisReport: analysis report.
    """
    return reports.AnalysisReport(
        plugin_name=self.NAME, text='TestMemory report')

  # pylint: disable=unused-argument
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
    self._objects.append(list(range(1024)))


manager.AnalysisPluginManager.RegisterPlugin(TestMemoryAnalysisPlugin)
