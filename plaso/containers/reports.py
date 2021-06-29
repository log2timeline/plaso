# -*- coding: utf-8 -*-
"""Report related attribute container definitions."""

from plaso.containers import interface
from plaso.containers import manager


class AnalysisReport(interface.AttributeContainer):
  """Analysis report attribute container.

  Attributes:
    analysis_counter (collections.Counter): counter of analysis results, for
         example number of events analyzed and tagged.
    event_filter (str): event filter expression that was used when the analysis
        plugin was run.
    filter_string (str): deprecated variant of event_filter.
    plugin_name (str): name of the analysis plugin that generated the report.
    report_dict (dict[str]): ???
    text (str): report text.
    time_compiled (int): timestamp of the date and time the report was compiled.
  """
  CONTAINER_TYPE = 'analysis_report'

  def __init__(self, plugin_name=None, text=None):
    """Initializes the analysis report.

    Args:
      plugin_name (Optional[str]): name of the analysis plugin that generated
          the report.
      text (Optional[str]): report text.
    """
    super(AnalysisReport, self).__init__()
    self.analysis_counter = None
    self.event_filter = None
    # TODO: filter_string is deprecated remove at some point.
    self.filter_string = None
    self.plugin_name = plugin_name
    self.report_dict = None
    # TODO: rename text to body?
    self.text = text
    self.time_compiled = None

  def CopyToDict(self):
    """Copies the attribute container to a dictionary.

    Returns:
      dict[str, object]: attribute values per name.
    """
    dictionary = {}
    for attribute_name, attribute_value in self.GetAttributes():
      if attribute_value is None:
        continue

      dictionary[attribute_name] = attribute_value

    return dictionary


manager.AttributeContainersManager.RegisterAttributeContainer(AnalysisReport)
