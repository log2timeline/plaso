# -*- coding: utf-8 -*-
"""A plugin that gather extension IDs from Chrome history browser."""

import logging
import re
import urllib2

from plaso.analysis import interface
from plaso.analysis import manager
from plaso.lib import event


class ChromeExtensionPlugin(interface.AnalysisPlugin):
  """Convert Chrome extension IDs into names, requires Internet connection."""

  NAME = 'chrome_extension'

  # Indicate that we can run this plugin during regular extraction.
  ENABLE_IN_EXTRACTION = True

  _TITLE_RE = re.compile('<title>([^<]+)</title>')
  _WEB_STORE_URL = u'https://chrome.google.com/webstore/detail/{xid}?hl=en-US'

  def __init__(self, incoming_queue):
    """Initializes the Chrome extension analysis plugin.

    Args:
      incoming_queue: A queue that is used to listen to incoming events.
    """
    super(ChromeExtensionPlugin, self).__init__(incoming_queue)

    self._results = {}
    self.plugin_type = self.TYPE_REPORT

    # TODO: see if these can be moved to arguments passed to ExamineEvent
    # or some kind of state object.
    self._sep = None
    self._user_paths = None

    # Saved list of already looked up extensions.
    self._extensions = {}

  def _GetChromeWebStorePage(self, extension_id):
    """Retrieves the page for the extension from the Chrome store website.

    Args:
      extension_id: string containing the extension identifier.
    """
    web_store_url = self._WEB_STORE_URL.format(xid=extension_id)
    try:
      response = urllib2.urlopen(web_store_url)

    except urllib2.HTTPError as exception:
      logging.warning((
          u'[{0:s}] unable to retrieve URL: {1:s} with error: {2:s}').format(
              self.NAME, web_store_url, exception))
      return

    except urllib2.URLError as exception:
      logging.warning((
          u'[{0:s}] invalid URL: {1:s} with error: {2:s}').format(
              self.NAME, web_store_url, exception))
      return

    return response

  def _GetTitleFromChromeWebStore(self, extension_id):
    """Retrieves the name of the extension from the Chrome store website.

    Args:
      extension_id: string containing the extension identifier.
    """
    # Check if we have already looked this extension up.
    if extension_id in self._extensions:
      return self._extensions.get(extension_id)

    response = self._GetChromeWebStorePage(extension_id)
    if not response:
      logging.warning(
          u'[{0:s}] no data returned for extension identifier: {1:s}'.format(
              self.NAME, extension_id))
      return

    first_line = response.readline()
    match = self._TITLE_RE.search(first_line)
    if match:
      title = match.group(1)
      if title.startswith(u'Chrome Web Store - '):
        name = title[19:]
      elif title.endswith(u'- Chrome Web Store'):
        name = title[:-19]

      self._extensions[extension_id] = name
      return name

    self._extensions[extension_id] = u'Not Found'

  def CompileReport(self, analysis_mediator):
    """Compiles a report of the analysis.

    Args:
      analysis_mediator: The analysis mediator object (instance of
                         AnalysisMediator).

    Returns:
      The analysis report (instance of AnalysisReport).
    """
    report = event.AnalysisReport(self.NAME)

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

  def ExamineEvent(self, analysis_mediator, event_object, **unused_kwargs):
    """Analyzes an event object.

    Args:
      analysis_mediator: The analysis mediator object (instance of
                         AnalysisMediator).
      event_object: An event object (instance of EventObject).
    """
    # Only interested in filesystem events.
    if event_object.data_type != 'fs:stat':
      return

    filename = getattr(event_object, 'filename', None)
    if not filename:
      return

    # Determine if we have a Chrome extension ID.
    if u'chrome' not in filename.lower():
      return

    if not self._sep:
      self._sep = analysis_mediator.GetPathSegmentSeparator(filename)

    if not self._user_paths:
      self._user_paths = analysis_mediator.GetUserPaths(analysis_mediator.users)

    if u'{0:s}Extensions{0:s}'.format(self._sep) not in filename:
      return

    # Now we have extension IDs, let's check if we've got the
    # folder, nothing else.
    paths = filename.split(self._sep)
    if paths[-2] != u'Extensions':
      return

    extension_id = paths[-1]
    if extension_id == u'Temp':
      return

    # Get the user and ID.
    user = analysis_mediator.GetUsernameFromPath(
        self._user_paths, filename, self._sep)

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


manager.AnalysisPluginManager.RegisterPlugin(ChromeExtensionPlugin)
