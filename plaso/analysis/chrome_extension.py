#!/usr/bin/python
# -*- coding: utf-8 -*-
#
# Copyright 2013 The Plaso Project Authors.
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
"""A plugin that gather extension ID's from Chrome history browser."""

import logging
import re
import urllib2

from plaso.analysis import interface
from plaso.lib import event


class AnalyzeChromeExtensionPlugin(interface.AnalysisPlugin):
  """Convert Chrome extension ID's into names, requires Internet connection."""

  NAME = 'chrome_extension'

  # Indicate that we can run this plugin during regular extraction.
  ENABLE_IN_EXTRACTION = True

  EXTENSION_NAME_RE = re.compile('<title>([^<]+) - Chrome Web Store</title>')
  WEB_STORE_URL = u'https://chrome.google.com/webstore/detail/{xid}?hl=en-US'

  def __init__(self, pre_obj, incoming_queue, outgoing_queue):
    """Constructor for the Chrome extension plugin."""
    super(AnalyzeChromeExtensionPlugin, self).__init__(
        pre_obj, incoming_queue, outgoing_queue)

    self._results = {}
    self.plugin_type = self.TYPE_REPORT
    self._sep = None
    self._user_paths = {}
    users = getattr(pre_obj, 'users', None)

    # Saved list of already looked up extensions.
    self._extensions = {}

    if users:
      user_separator = None
      for user in users:
        name = user.get('name')
        path = user.get('path')

        if not path or not name:
          continue

        if not user_separator:
          user_separator = self._GetSeparator(path)

        if user_separator != '/':
          path = path.replace(user_separator, '/').replace('//', '/')

        if path[1:].startswith(':/'):
          path = path[2:]

        self._user_paths[name.lower()] = path.lower()

  def _GetSeparator(self, path):
    """Given a path give back the path separator as a best guess."""
    if path.startswith('\\') or path[1:].startswith(':\\'):
      return '\\'

    if path.startswith('/'):
      return '/'

    if '/' and '\\' in path:
      # Let's count slashes and guess which one is the right one.
      forward_count = len(path.split('/'))
      backward_count = len(path.split('\\'))

      if forward_count > backward_count:
        return '/'
      else:
        return '\\'

    # Now we are sure there is only one type of separators yet
    # the path does not start with one.
    if '/' in path:
      return '/'
    else:
      return '\\'

  def _GetUserNameFromPath(self, file_path):
    """Return a username based on gathered information in pre_obj and path.

    During preprocessing the tool will gather file paths to where each user
    profile is stored, and which user it belongs to. This function takes in
    a path to a file and compares it to a list of all discovered usernames
    and paths to their profiles in the system. If it finds that the file path
    belongs to a user profile it will return the username that the profile
    belongs to.

    Args:
      file_path: The full path to the file being anayzed.

    Returns:
      If possible the responsible username behind the file. Otherwise None.
    """
    if not self._user_paths:
      return

    if self._sep != '/':
      use_path = file_path.replace(self._sep, '/')
    else:
      use_path = file_path

    if use_path[1:].startswith(':/'):
      use_path = use_path[2:]

    use_path = use_path.lower()

    for user, path in self._user_paths.iteritems():
      if use_path.startswith(path):
        return user

  def _GetTitleFromChromeWebStore(self, extension_id):
    """Read the extension name from a Chrome store for a given extension ID."""
    # Check if we have already looked this extension up.
    if extension_id in self._extensions:
      return self._extensions.get(extension_id)

    try:
      response = urllib2.urlopen(self.WEB_STORE_URL.format(xid=extension_id))
    except urllib2.HTTPError as exception:
      logging.warning((
          u'Unable to retrieve results from URL: {1:s} with '
          u'error: {0:s}').format(
              exception, self.WEB_STORE_URL.format(xid=extension_id)))
      return
    except urllib2.URLError as exception:
      logging.warning(u'Not a valid Extension ID with error: {0:s}'.format(
          exception))
      return

    first_line = response.readline()
    match = self.EXTENSION_NAME_RE.search(first_line)
    if match:
      name = match.group(1)
      self._extensions[extension_id] = name
      return name

    self._extensions[extension_id] = 'Not Found'

  def ExamineEvent(self, event_object):
    """Take an EventObject and send it through analysis."""
    # Only interested in filesystem events.
    if event_object.data_type != 'fs:stat':
      return

    filename = getattr(event_object, 'filename', None)

    if not filename:
      return

    # Determine if we have a Chrome extension ID.
    if 'chrome' not in filename.lower():
      return

    if not self._sep:
      self._sep = self._GetSeparator(filename)

    if u'{0:s}Extensions{0:s}'.format(self._sep) not in filename:
      return

    # Now we have extension ID's, let's check if we've got the
    # folder, nothing else.
    paths = filename.split(self._sep)
    if paths[-2] != 'Extensions':
      return

    extension_id = paths[-1]

    if extension_id == 'Temp':
      return

    # Get the user and ID.
    user = self._GetUserNameFromPath(filename)
    # We still want this information in here, so that we can
    # manually deduce the username.
    if not user:
      if len(filename) > 25:
        user = u'Not found ({0:s}...)'.format(filename[0:25])
      else:
        user = u'Not found ({0:s})'.format(filename)

    extension = self._GetTitleFromChromeWebStore(extension_id)

    if not extension:
      extension = extension_id

    self._results.setdefault(user, [])
    extension_string = extension.decode('utf-8', 'ignore')
    if (extension_string, extension_id) not in self._results[user]:
      self._results[user].append((extension_string, extension_id))

  def CompileReport(self):
    """Compiles a report of the analysis.

    Returns:
      The analysis report (instance of AnalysisReport).
    """
    report = event.AnalysisReport()

    report.report_dict = self._results

    lines_of_text = []
    for user, extensions in sorted(self._results.iteritems()):
      lines_of_text.append(u' == USER: {0:s} =='.format(user))
      for extension, extension_id in sorted(extensions):
        lines_of_text.append(u'  {0:s} [{1:s}]'.format(extension, extension_id))

      # An empty string is added to have SetText create an empty line.
      lines_of_text.append(u'')

    report.SetText(lines_of_text)

    return report
