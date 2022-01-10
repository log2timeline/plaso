# -*- coding: utf-8 -*-
"""Analysis plugin that labels events according to rules in a tagging file."""

from plaso.analysis import interface
from plaso.analysis import manager
from plaso.engine import tagging_file


class TaggingAnalysisPlugin(interface.AnalysisPlugin):
  """Analysis plugin that labels events according to rules in a tagging file."""

  NAME = 'tagging'

  def __init__(self):
    """Initializes a tagging analysis plugin."""
    super(TaggingAnalysisPlugin, self).__init__()
    self._tagging_rules = None

  def ExamineEvent(
      self, analysis_mediator, event, event_data, event_data_stream):
    """Labels events according to the rules in a tagging file.

    Args:
      analysis_mediator (AnalysisMediator): mediates interactions between
          analysis plugins and other components, such as storage and dfVFS.
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

      analysis_mediator.ProduceEventTag(event_tag)

      for label_name in matched_label_names:
        self._analysis_counter[label_name] += 1

      self._analysis_counter['event_tags'] += 1

  def SetAndLoadTagFile(self, tagging_file_path):
    """Sets the tagging file to be used by the plugin.

    Args:
      tagging_file_path (str): path of the tagging file.
    """
    tagging_file_object = tagging_file.TaggingFile(tagging_file_path)
    self._tagging_rules = tagging_file_object.GetEventTaggingRules()


manager.AnalysisPluginManager.RegisterPlugin(TaggingAnalysisPlugin)
