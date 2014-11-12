#!/usr/bin/python
# -*- coding: utf-8 -*-
#
# Copyright 2014 The Plaso Project Authors.
# Please see the AUTHORS file for details on individual authors.
#
# Licensed under the Apache License, Version 2.0 (the "License");
# you may not use this file except in compliance with the License.
# You may obtain a copy of the License at
#
#    http://www.apache.org/licenses/LICENSE-2.0
#
# Unless required by applicable law or agreed to in writing, software
# distributed under the License is distributed on an "AS IS" BASIS,
# WITHOUT WARRANTIES OR CONDITIONS OF ANY KIND, either express or implied.
# See the License for the specific language governing permissions and
# limitations under the License.
"""The analysis context object."""


class AnalysisContext(object):
  """Class that implements the analysis context."""

  def __init__(self, analysis_report_queue_producer, knowledge_base):
    """Initializes a analysis plugin context object.

    Args:
      analysis_report_queue_producer: the analysis report queue producer
                                      (instance of ItemQueueProducer).
      knowledge_base: A knowledge base object (instance of KnowledgeBase),
                      which contains information from the source data needed
                      for analysis.
    """
    super(AnalysisContext, self).__init__()
    self._analysis_report_queue_producer = analysis_report_queue_producer
    self._knowledge_base = knowledge_base

    self.number_of_produced_analysis_reports = 0

  @property
  def users(self):
    """The list of users."""
    return self._knowledge_base.users

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
      name = user.get('name')
      path = user.get('path')

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
    if not getattr(analysis_report, 'plugin_name', None) and plugin_name:
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
