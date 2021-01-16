# -*- coding: utf-8 -*-
"""A plugin to tag events according to rules in a tagging file."""

from plaso.analysis import interface
from plaso.analysis import manager
from plaso.containers import reports
from plaso.engine import tagging_file


class TaggingAnalysisPlugin(interface.AnalysisPlugin):
  """Analysis plugin that tags events according to rules in a tagging file."""

  NAME = 'tagging'

  def __init__(self):
    """Initializes a tagging analysis plugin."""
    super(TaggingAnalysisPlugin, self).__init__()
    self._number_of_event_tags = 0
    self._tagging_rules = None

  def CompileReport(self, mediator):
    """Compiles an analysis report.

    Args:
      mediator (AnalysisMediator): mediates interactions between
          analysis plugins and other components, such as storage and dfvfs.

    Returns:
      AnalysisReport: analysis report.
    """
    report_text = 'Tagging plugin produced {0:d} tags.\n'.format(
        self._number_of_event_tags)
    self._number_of_event_tags = 0
    return reports.AnalysisReport(plugin_name=self.NAME, text=report_text)

  def ExamineEvent(self, mediator, event, event_data, event_data_stream):
    """Analyzes an EventObject and tags it according to rules in the tag file.

    Args:
      mediator (AnalysisMediator): mediates interactions between analysis
          plugins and other components, such as storage and dfvfs.
      event (EventObject): event to examine.
      event_data (EventData): event data.
      event_data_stream (EventDataStream): event data stream.
    """
    matched_label_names = []
    for label_name, filter_objects in self._tagging_rules.items():
      for filter_object in filter_objects:
        # Note that tagging events based on existing labels is currently
        # not supported.
        if filter_object.Match(event, event_data, event_data_stream, None):
          matched_label_names.append(label_name)
          break

    if matched_label_names:
      event_tag = self._CreateEventTag(event, matched_label_names)

      mediator.ProduceEventTag(event_tag)
      self._number_of_event_tags += 1

  def SetAndLoadTagFile(self, tagging_file_path):
    """Sets the tag file to be used by the plugin.

    Args:
      tagging_file_path (str): path of the tagging file.
    """
    tag_file = tagging_file.TaggingFile(tagging_file_path)
    self._tagging_rules = tag_file.GetEventTaggingRules()


manager.AnalysisPluginManager.RegisterPlugin(TaggingAnalysisPlugin)
