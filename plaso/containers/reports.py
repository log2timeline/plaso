# -*- coding: utf-8 -*-
"""Report related attribute container definitions."""

from acstore.containers import interface
from acstore.containers import manager


class AnalysisReport(interface.AttributeContainer):
  """Analysis report attribute container.

  Attributes:
    analysis_counter (collections.Counter): counter of analysis results, for
         example number of events analyzed and tagged.
    event_filter (str): event filter expression that was used when the analysis
        plugin was run.
    plugin_name (str): name of the analysis plugin that generated the report.
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
    self.plugin_name = plugin_name
    # TODO: kept for backwards compatibility.
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
