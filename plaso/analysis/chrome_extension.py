# -*- coding: utf-8 -*-
"""A plugin that gather extension IDs from Chrome history browser."""

import logging
import re

import requests

from plaso.analysis import interface
from plaso.analysis import manager
from plaso.containers import reports


class ChromeExtensionPlugin(interface.AnalysisPlugin):
  """Convert Chrome extension IDs into names, requires Internet connection."""

  NAME = u'chrome_extension'

  # Indicate that we can run this plugin during regular extraction.
  ENABLE_IN_EXTRACTION = True

  _TITLE_RE = re.compile(r'<title>([^<]+)</title>')
  _WEB_STORE_URL = u'https://chrome.google.com/webstore/detail/{xid}?hl=en-US'

  def __init__(self):
    """Initializes the Chrome extension analysis plugin."""
    super(ChromeExtensionPlugin, self).__init__()

    # Saved list of already looked up extensions.
    self._extensions = {}
    self._results = {}

    # TODO: see if these can be moved to arguments passed to ExamineEvent
    # or some kind of state object.
    self._sep = None

  def _GetChromeWebStorePage(self, extension_identifier):
    """Retrieves the page for the extension from the Chrome store website.

    Args:
      extension_identifier (str): Chrome extension identifier.

    Returns:
      str: page content or None.
    """
    web_store_url = self._WEB_STORE_URL.format(xid=extension_identifier)
    try:
      response = requests.get(web_store_url)

    except (requests.ConnectionError, requests.HTTPError) as exception:
      logging.warning((
          u'[{0:s}] unable to retrieve URL: {1:s} with error: {2:s}').format(
              self.NAME, web_store_url, exception))
      return

    return response.text

  def _GetPathSegmentSeparator(self, path):
    """Given a path give back the path separator as a best guess.

    Args:
      path (str): path.

    Returns:
      str: path segment separator.
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

  def _GetTitleFromChromeWebStore(self, extension_identifier):
    """Retrieves the name of the extension from the Chrome store website.

    Args:
      extension_identifier (str): Chrome extension identifier.

    Returns:
      str: name of the extension or None.
    """
    # Check if we have already looked this extension up.
    if extension_identifier in self._extensions:
      return self._extensions.get(extension_identifier)

    page_content = self._GetChromeWebStorePage(extension_identifier)
    if not page_content:
      logging.warning(
          u'[{0:s}] no data returned for extension identifier: {1:s}'.format(
              self.NAME, extension_identifier))
      return

    first_line, _, _ = page_content.partition(b'\n')
    match = self._TITLE_RE.search(first_line)
    name = None
    if match:
      title = match.group(1)
      if title.startswith(b'Chrome Web Store - '):
        name = title[19:]
      elif title.endswith(b'- Chrome Web Store'):
        name = title[:-19]

    if not name:
      self._extensions[extension_identifier] = u'UNKNOWN'
      return

    name = name.decode(u'utf-8', errors=u'replace')
    self._extensions[extension_identifier] = name
    return name

  def CompileReport(self, mediator):
    """Compiles an analysis report.

    Args:
      mediator (AnalysisMediator): mediates interactions between analysis
          plugins and other components, such as storage and dfvfs.

    Returns:
      AnalysisReport: analysis report.
    """
    lines_of_text = []
    for user, extensions in sorted(self._results.items()):
      lines_of_text.append(u' == USER: {0:s} =='.format(user))
      for extension, extension_identifier in sorted(extensions):
        lines_of_text.append(u'  {0:s} [{1:s}]'.format(
            extension, extension_identifier))
      lines_of_text.append(u'')

    lines_of_text.append(u'')
    report_text = u'\n'.join(lines_of_text)
    analysis_report = reports.AnalysisReport(
        plugin_name=self.NAME, text=report_text)
    analysis_report.report_dict = self._results
    return analysis_report

  def ExamineEvent(self, mediator, event):
    """Analyzes an event.

    Args:
      mediator (AnalysisMediator): mediates interactions between analysis
          plugins and other components, such as storage and dfvfs.
      event (EventObject): event to examine.
    """
    # Only interested in filesystem events.
    if event.data_type != u'fs:stat':
      return

    filename = getattr(event, u'filename', None)
    if not filename:
      return

    # Determine if we have a Chrome extension ID.
    if u'chrome' not in filename.lower():
      return

    if not self._sep:
      self._sep = self._GetPathSegmentSeparator(filename)

    if u'{0:s}Extensions{0:s}'.format(self._sep) not in filename:
      return

    # Now we have extension IDs, let's check if we've got the
    # folder, nothing else.
    paths = filename.split(self._sep)
    if paths[-2] != u'Extensions':
      return

    extension_identifier = paths[-1]
    if extension_identifier == u'Temp':
      return

    # Get the user and ID.
    user = mediator.GetUsernameForPath(filename)

    # We still want this information in here, so that we can
    # manually deduce the username.
    if not user:
      if len(filename) > 25:
        user = u'Not found ({0:s}...)'.format(filename[0:25])
      else:
        user = u'Not found ({0:s})'.format(filename)

    extension = self._GetTitleFromChromeWebStore(extension_identifier)
    if not extension:
      extension = extension_identifier

    self._results.setdefault(user, [])
    extension_string = extension.decode(u'utf-8', errors=u'ignore')
    if (extension_string, extension_identifier) not in self._results[user]:
      self._results[user].append((extension_string, extension_identifier))


manager.AnalysisPluginManager.RegisterPlugin(ChromeExtensionPlugin)
