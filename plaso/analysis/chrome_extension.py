# -*- coding: utf-8 -*-
"""A plugin that gather extension IDs from Chrome history browser."""

from __future__ import unicode_literals

import re

import requests

from plaso.analysis import interface
from plaso.analysis import logger
from plaso.analysis import manager
from plaso.containers import reports


class ChromeExtensionPlugin(interface.AnalysisPlugin):
  """Convert Chrome extension IDs into names, requires Internet connection."""

  NAME = 'chrome_extension'

  # Indicate that we can run this plugin during regular extraction.
  ENABLE_IN_EXTRACTION = True

  _SUPPORTED_EVENT_DATA_TYPES = frozenset([
      'fs:stat'])

  _TITLE_RE = re.compile(r'<title>([^<]+)</title>')
  _WEB_STORE_URL = 'https://chrome.google.com/webstore/detail/{xid}?hl=en-US'

  def __init__(self):
    """Initializes the Chrome extension analysis plugin."""
    super(ChromeExtensionPlugin, self).__init__()

    # Saved list of already looked up extensions.
    self._extensions = {}
    self._results = {}

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
      logger.warning((
          '[{0:s}] unable to retrieve URL: {1:s} with error: {2!s}').format(
              self.NAME, web_store_url, exception))
      return None

    return response.text

  def _GetPathSegmentSeparator(self, path):
    """Given a path give back the path separator as a best guess.

    Args:
      path (str): path.

    Returns:
      str: path segment separator.
    """
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

      return '\\'

    # Now we are sure there is only one type of separators yet
    # the path does not start with one.
    if '/' in path:
      return '/'

    return '\\'

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
      logger.warning(
          '[{0:s}] no data returned for extension identifier: {1:s}'.format(
              self.NAME, extension_identifier))
      return None

    first_line, _, _ = page_content.partition('\n')
    match = self._TITLE_RE.search(first_line)
    name = None
    if match:
      title = match.group(1)
      if title.startswith('Chrome Web Store - '):
        name = title[19:]
      elif title.endswith('- Chrome Web Store'):
        name = title[:-19]

    if not name:
      self._extensions[extension_identifier] = 'UNKNOWN'
      return None

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
      lines_of_text.append(' == USER: {0:s} =='.format(user))
      for extension, extension_identifier in sorted(extensions):
        lines_of_text.append('  {0:s} [{1:s}]'.format(
            extension, extension_identifier))
      lines_of_text.append('')

    lines_of_text.append('')
    report_text = '\n'.join(lines_of_text)
    analysis_report = reports.AnalysisReport(
        plugin_name=self.NAME, text=report_text)
    analysis_report.report_dict = self._results
    return analysis_report

  # pylint: disable=unused-argument
  def ExamineEvent(self, mediator, event, event_data):
    """Analyzes an event.

    Args:
      mediator (AnalysisMediator): mediates interactions between analysis
          plugins and other components, such as storage and dfvfs.
      event (EventObject): event to examine.
      event_data (EventData): event data.
    """
    if event_data.data_type not in self._SUPPORTED_EVENT_DATA_TYPES:
      return

    filename = getattr(event_data, 'filename', None)
    if not filename:
      return

    separator = self._GetPathSegmentSeparator(filename)
    path_segments = filename.lower().split(separator)

    # Determine if we have a Chrome extension ID.
    if 'chrome' not in path_segments and 'chromium' not in path_segments:
      return

    if path_segments[-2] != 'extensions':
      return

    # TODO: use a regex to check extension identifier
    extension_identifier = path_segments[-1]
    if extension_identifier == 'Temp':
      return

    user = mediator.GetUsernameForPath(filename)

    # We still want this information in here, so that we can
    # manually deduce the username.
    if not user:
      if len(filename) > 25:
        user = 'Not found ({0:s}...)'.format(filename[0:25])
      else:
        user = 'Not found ({0:s})'.format(filename)

    extension_string = self._GetTitleFromChromeWebStore(extension_identifier)
    if not extension_string:
      extension_string = extension_identifier

    self._results.setdefault(user, [])
    if (extension_string, extension_identifier) not in self._results[user]:
      self._results[user].append((extension_string, extension_identifier))


manager.AnalysisPluginManager.RegisterPlugin(ChromeExtensionPlugin)
