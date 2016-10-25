# -*- coding: utf-8 -*-
"""The analysis plugin mediator object."""

from plaso.lib import timelib


class AnalysisMediator(object):
  """Class that implements the analysis plugin mediator.

  Attributes:
    number_of_produced_analysis_reports (int): number of produced analysis
        reports.
    number_of_produced_event_tags (int): number of produced event tags.
  """

  def __init__(self, storage_writer, knowledge_base, data_location=None):
    """Initializes an analysis plugin mediator object.

    Args:
      storage_writer (StorageWriter): storage writer.
      knowledge_base (KnowledgeBase): contains information from the source
          data needed for analysis.
      data_location (Optional[str]): location of data files used during
          analysis.
    """
    super(AnalysisMediator, self).__init__()
    self._abort = False
    self._data_location = data_location
    self._event_filter_expression = None
    self._knowledge_base = knowledge_base
    self._storage_writer = storage_writer

    self.number_of_produced_analysis_reports = 0
    self.number_of_produced_event_tags = 0

  @property
  def abort(self):
    """bool: True if the analysis should be aborted."""
    return self._abort

  @property
  def data_location(self):
    """str: path to the data files."""
    return self._data_location

  @property
  def platform(self):
    """str: platform."""
    return self._knowledge_base.platform

  def GetDisplayName(self, path_spec):
    """Retrieves the display name for the path spec.

    Args:
      path_spec (dfvfs.PathSpec): paths specification.

    Returns:
      str: human readable path.
    """
    relative_path = self.GetRelativePath(path_spec)

    return u'{0:s}:{1:s}'.format(path_spec.type_indicator, relative_path)

  def GetRelativePath(self, path_spec):
    """Retrieves the relative path of a path specification.

    Args:
      path_spec (dfvfs.PathSpec): paths specification.

    Returns:
      str: relative path or None.
    """
    # TODO: Solve this differently, quite possibly inside dfVFS using mount
    # path spec.
    file_path = getattr(path_spec, u'location', None)
    # TODO: Determine if we need to access the mount_path, as for the parser
    # mediator.
    return file_path

  def GetUsernameForPath(self, path):
    """Retrieves a username for a specific path.

    This is determining if a specific path is within a user's directory and
    returning the username of the user if so.

    Args:
      path (str): path.

    Returns:
      str: username or None if the path does not appear to be within a user's
          directory.
    """
    return self._knowledge_base.GetUsernameForPath(path)

  def ProduceAnalysisReport(self, plugin):
    """Produces an analysis report.

    Args:
      plugin (AnalysisPlugin): plugin.
    """
    analysis_report = plugin.CompileReport(self)
    if not analysis_report:
      return

    analysis_report.time_compiled = timelib.Timestamp.GetNow()

    plugin_name = getattr(analysis_report, u'plugin_name', plugin.plugin_name)
    if plugin_name:
      analysis_report.plugin_name = plugin_name

    if self._event_filter_expression:
      # TODO: rename filter string when refactoring the analysis reports.
      analysis_report.filter_string = self._event_filter_expression

    self._storage_writer.AddAnalysisReport(analysis_report)

    self.number_of_produced_analysis_reports += 1
    self.number_of_produced_event_tags = (
        self._storage_writer.number_of_event_tags)

  def ProduceEventTag(self, event_tag):
    """Produces an event tag.

    Args:
      event_tag (EventTag): event tag.
    """
    self._storage_writer.AddEventTag(event_tag)

    self.number_of_produced_event_tags += 1

  def SignalAbort(self):
    """Signals the analysis plugins to abort."""
    self._abort = True
