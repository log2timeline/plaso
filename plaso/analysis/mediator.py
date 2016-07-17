# -*- coding: utf-8 -*-
"""The analysis plugin mediator object."""


class AnalysisMediator(object):
  """Class that implements the analysis plugin mediator.

  Attributes:
    number_of_produced_analysis_reports (int): number of produced analysis
        reports.
  """

  def __init__(
      self, analysis_report_queue_producer, knowledge_base,
      data_location=None, completion_event=None):
    """Initializes an analysis plugin mediator object.

    Args:
      analysis_report_queue_producer (ItemQueueProducer): analysis report
          queue producer.
      knowledge_base (KnowledgeBase): knowledge base, which contains
          information from the source data needed for parsing.
      data_location (Optional[str]): location of the data files.
      completion_event (Optional[Multiprocessing.Event]): multi processing event
          that will be set when the analysis plugin is complete.
    """
    super(AnalysisMediator, self).__init__()
    self._analysis_report_queue_producer = analysis_report_queue_producer
    self._completion_event = completion_event
    self._data_location = data_location
    self._knowledge_base = knowledge_base

    self.number_of_produced_analysis_reports = 0

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

    This method compares the path with the user directories. The the path
    has the same location as a user directory the corresponding username
    is returned.

    Args:
      path (str): path.

    Returns:
      str: username or None.
    """
    return self._knowledge_base.GetUsernameForPath(path)

  def ProcessAnalysisReport(self, analysis_report, plugin_name=None):
    """Processes an analysis report before it is emitted to the queue.

    Args:
      analysis_report (AnalysisReport): analysis report.
      plugin_name (Optional[str]): name of the plugin.
    """
    if not getattr(analysis_report, u'plugin_name', None) and plugin_name:
      analysis_report.plugin_name = plugin_name

  def ProduceAnalysisReport(self, analysis_report, plugin_name=None):
    """Produces an analysis report onto the queue.

    Args:
      analysis_report (AnalysisReport): analysis report.
      plugin_name (Optional[str]): name of the plugin.
    """
    self.ProcessAnalysisReport(analysis_report, plugin_name=plugin_name)

    self._analysis_report_queue_producer.ProduceItem(analysis_report)
    self.number_of_produced_analysis_reports += 1

  def ReportingComplete(self):
    """Called by an analysis plugin to signal that it has generated its report.

    This method signals to report consumers that no further reports will be
    produced by the analysis plugin.
    """
    if self._completion_event:
      self._completion_event.set()
    self._analysis_report_queue_producer.Close()
