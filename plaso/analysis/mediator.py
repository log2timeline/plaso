# -*- coding: utf-8 -*-
"""The analysis plugin mediator object."""

import collections
import time

from plaso.containers import warnings
from plaso.engine import path_helper


class AnalysisMediator(object):
  """Analysis plugin mediator.

  Attributes:
    analysis_reports_counter (collections.Counter): number of analysis reports
        per analysis plugin.
    event_labels_counter (collections.Counter): number of event tags per label.
    last_activity_timestamp (int): timestamp received that indicates the last
        time activity was observed. The last activity timestamp is updated
        when the mediator produces an attribute container, such as an event
        tag. This timestamp is used by the multi processing worker process
        to indicate the last time the worker was known to be active. This
        information is then used by the foreman to detect workers that are
        not responding (stalled).
    number_of_produced_analysis_reports (int): number of produced analysis
        reports.
    number_of_produced_event_tags (int): number of produced event tags.
  """

  def __init__(self, data_location=None, user_accounts=None):
    """Initializes an analysis plugin mediator.

    Args:
      data_location (Optional[str]): location of data files used during
          analysis.
      user_accounts (Optional[list[UserAccountArtifact]]): user accounts.
    """
    super(AnalysisMediator, self).__init__()
    self._abort = False
    self._data_location = data_location
    self._event_filter_expression = None
    self._number_of_warnings = 0
    self._storage_writer = None
    self._user_accounts = user_accounts
    self._username_by_user_directory = {}

    self.analysis_reports_counter = collections.Counter()
    self.event_labels_counter = collections.Counter()
    self.last_activity_timestamp = 0.0
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

  def GetDisplayNameForPathSpec(self, path_spec):
    """Retrieves the display name for a path specification.

    Args:
      path_spec (dfvfs.PathSpec): path specification.

    Returns:
      str: human readable version of the path specification.
    """
    return path_helper.PathHelper.GetDisplayNameForPathSpec(path_spec)

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
    path = path.lower()

    username = self._username_by_user_directory.get(path, None)
    if not username and self._user_accounts:
      for user_account in self._user_accounts:
        if user_account.user_directory:
          user_directory = user_account.user_directory.lower()
          if path.startswith(user_directory):
            username = user_account.username
            self._username_by_user_directory[path] = username
            break

    return username

  def ProduceAnalysisResult(self, analysis_result):
    """Produces an analysis result attribute.

    Args:
      analysis_result (AttributeContainer): analysis result.
    """
    if self._storage_writer:
      self._storage_writer.AddAttributeContainer(analysis_result)

  def ProduceAnalysisReport(self, plugin):
    """Produces an analysis report.

    Args:
      plugin (AnalysisPlugin): plugin.
    """
    analysis_report = plugin.CompileReport(self)
    if not analysis_report:
      # TODO: produce AnalysisWarning that no report can be generated.
      return

    analysis_report.event_filter = self._event_filter_expression

    if self._storage_writer:
      self._storage_writer.AddAttributeContainer(analysis_report)

    self.analysis_reports_counter[analysis_report.plugin_name] += 1
    self.analysis_reports_counter['total'] += 1

    self.number_of_produced_analysis_reports += 1

    self.last_activity_timestamp = time.time()

  def ProduceAnalysisWarning(self, message, plugin_name):
    """Produces an analysis warning.

    Args:
      message (str): message of the warning.
      plugin_name (str): name of the analysis plugin to which the warning
          applies.
    """
    if self._storage_writer:
      warning = warnings.AnalysisWarning(
         message=message, plugin_name=plugin_name)
      self._storage_writer.AddAttributeContainer(warning)

    self._number_of_warnings += 1

    self.last_activity_timestamp = time.time()

  def ProduceEventTag(self, event_tag):
    """Produces an event tag.

    Args:
      event_tag (EventTag): event tag.
    """
    if self._storage_writer:
      self._storage_writer.AddOrUpdateEventTag(event_tag)

    for label in event_tag.labels:
      self.event_labels_counter[label] += 1
      self.event_labels_counter['total'] += 1

    self.number_of_produced_event_tags += 1

    self.last_activity_timestamp = time.time()

  def SetStorageWriter(self, storage_writer):
    """Sets the storage writer.

    Args:
      storage_writer (StorageWriter): storage writer.
    """
    self._storage_writer = storage_writer

  def SignalAbort(self):
    """Signals the analysis plugins to abort."""
    self._abort = True
