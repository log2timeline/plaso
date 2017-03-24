# -*- coding: utf-8 -*-
"""Report related attribute container object definitions."""

from plaso.containers import interface
from plaso.containers import manager
from plaso.lib import timelib


class AnalysisReport(interface.AttributeContainer):
  """Class to represent an analysis report attribute container.

  Attributes:
    filter_string: a string containing ???
    images: a list containing ???
    plugin_name: a string containing the name of the analysis plugin that
                 generated the report.
    report_array: an array containing ???
    report_dict: a dictionary containing ???
    text: a string containing the report text or None.
    time_compiled: a timestamp containing the date and time the report was
                   compiled.
  """
  CONTAINER_TYPE = u'analysis_report'

  def __init__(self, plugin_name=None, text=None):
    """Initializes the analysis report.

    Args:
      plugin_name: optional string containing the name of the analysis plugin
                   that generated the report.
      text: optional string containing the report text.
    """
    super(AnalysisReport, self).__init__()
    self.filter_string = None
    self.images = None
    self.plugin_name = plugin_name
    self.report_array = None
    self.report_dict = None
    # TODO: rename text to body?
    self.text = text
    self.time_compiled = None

  def CopyToDict(self):
    """Copies the attribute container to a dictionary.

    Returns:
      A dictionary containing the attribute container attributes.
    """
    dictionary = {}
    for attribute_name in iter(self.__dict__.keys()):
      attribute_value = getattr(self, attribute_name, None)
      if attribute_value is None:
        continue

      dictionary[attribute_name] = attribute_value

    return dictionary

  def GetString(self):
    """Retrievs a string representation of the report.

    Returns:
      A string containing the report.
    """
    # TODO: Make this a more complete function that includes images
    # and the option of saving as a full fledged HTML document.
    string_list = []
    string_list.append(u'Report generated from: {0:s}'.format(self.plugin_name))

    time_compiled = getattr(self, u'time_compiled', 0)
    if time_compiled:
      time_compiled = timelib.Timestamp.CopyToIsoFormat(time_compiled)
      string_list.append(u'Generated on: {0:s}'.format(time_compiled))

    filter_string = getattr(self, u'filter_string', u'')
    if filter_string:
      string_list.append(u'Filter String: {0:s}'.format(filter_string))

    string_list.append(u'')
    string_list.append(u'Report text:')
    string_list.append(self.text)

    return u'\n'.join(string_list)


manager.AttributeContainersManager.RegisterAttributeContainer(AnalysisReport)
