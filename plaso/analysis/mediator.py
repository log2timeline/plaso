# -*- coding: utf-8 -*-
"""The analysis plugin mediator object."""


class AnalysisMediator(object):
  """Class that implements the analysis plugin mediator."""

  # TODO: create output format definitions.
  def __init__(
      self, analysis_report_queue_producer, knowledge_base,
      output_format=u'text'):
    """Initializes an analysis plugin mediator object.

    Args:
      analysis_report_queue_producer: the analysis report queue producer
                                      (instance of ItemQueueProducer).
      knowledge_base: A knowledge base object (instance of KnowledgeBase),
                      which contains information from the source data needed
                      for analysis.
      output_format: Optional output format. The default is 'text'.
    """
    super(AnalysisMediator, self).__init__()
    self._analysis_report_queue_producer = analysis_report_queue_producer
    self._knowledge_base = knowledge_base
    self._output_format = output_format

    self.number_of_produced_analysis_reports = 0

  @property
  def output_format(self):
    """The output format."""
    return self._output_format

  @property
  def users(self):
    """The list of users."""
    return self._knowledge_base.users

  def GetRelativePath(self, path_spec):
    """Retrieves the relative path of the path spec.

    Args:
      path_spec: a PathSpec object (instance of dfvfs.PathSpec).

    Returns:
      A string containing the relative path or None.
    """
    # TODO: Solve this differently, quite possibly inside dfVFS using mount
    # path spec.
    file_path = getattr(path_spec, u'location', None)
    # TODO: Determine if we need to access the mount_path, as for the parser
    # mediator.
    return file_path

  def GetDisplayName(self, path_spec):
    """Retrieves the display name for the path spec.

    Args:
      file_entry: PathSpec object (instance of dfvfs.PathSpec).

    Returns:
      A human readable string that describes the path to the path spec.
    """
    relative_path = self.GetRelativePath(path_spec)

    return u'{0:s}:{1:s}'.format(path_spec.type_indicator, relative_path)

  def GetPathSegmentSeparator(self, path):
    """Given a path give back the path separator as a best guess.

    Args:
      path: the path.

    Returns:
      The path segment separator.
    """
    if path.startswith(u'\\') or path[1:].startswith(u':\\'):
      return u'\\'

    if path.startswith(u'/'):
      return u'/'

    if u'/' and u'\\' in path:
      # Let's count slashes and guess which one is the right one.
      forward_count = len(path.split(u'/'))
      backward_count = len(path.split(u'\\'))

      if forward_count > backward_count:
        return u'/'
      else:
        return u'\\'

    # Now we are sure there is only one type of separators yet
    # the path does not start with one.
    if u'/' in path:
      return u'/'
    else:
      return u'\\'

  def GetUsernameFromPath(self, user_paths, file_path, path_segment_separator):
    """Return a username based on preprocessing and the path.

    During preprocessing the tool will gather file paths to where each user
    profile is stored, and which user it belongs to. This function takes in
    a path to a file and compares it to a list of all discovered usernames
    and paths to their profiles in the system. If it finds that the file path
    belongs to a user profile it will return the username that the profile
    belongs to.

    Args:
      user_paths: A dictionary object containing the paths per username.
      file_path: The full path to the file being analyzed.
      path_segment_separator: String containing the path segment separator.

    Returns:
      If possible the responsible username behind the file. Otherwise None.
    """
    if not user_paths:
      return

    if path_segment_separator != u'/':
      use_path = file_path.replace(path_segment_separator, u'/')
    else:
      use_path = file_path

    if use_path[1:].startswith(u':/'):
      use_path = use_path[2:]

    use_path = use_path.lower()

    for user, path in user_paths.iteritems():
      if use_path.startswith(path):
        return user

  def GetUserPaths(self, users):
    """Retrieves the user paths.

    Args:
      users: a list of users.

    Returns:
      A dictionary object containing the paths per username or None if no users.
    """
    if not users:
      return

    user_paths = {}

    user_separator = None
    for user in users:
      name = user.get(u'name')
      path = user.get(u'path')

      if not path or not name:
        continue

      if not user_separator:
        user_separator = self.GetPathSegmentSeparator(path)

      if user_separator != u'/':
        path = path.replace(user_separator, u'/').replace(u'//', u'/')

      if path[1:].startswith(u':/'):
        path = path[2:]

      name = name.lower()
      user_paths[name] = path.lower()

    return user_paths

  def ProcessAnalysisReport(self, analysis_report, plugin_name=None):
    """Processes an analysis report before it is emitted to the queue.

    Args:
      analysis_report: the analysis report object (instance of AnalysisReport).
      plugin_name: Optional name of the plugin. The default is None.
    """
    if not getattr(analysis_report, u'plugin_name', None) and plugin_name:
      analysis_report.plugin_name = plugin_name

  def ProduceAnalysisReport(self, analysis_report, plugin_name=None):
    """Produces an analysis report onto the queue.

    Args:
      analysis_report: the analysis report object (instance of AnalysisReport).
      plugin_name: Optional name of the plugin. The default is None.
    """
    self.ProcessAnalysisReport(analysis_report, plugin_name=plugin_name)

    self._analysis_report_queue_producer.ProduceItem(analysis_report)
    self.number_of_produced_analysis_reports += 1
