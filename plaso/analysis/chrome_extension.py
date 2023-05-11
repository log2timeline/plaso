# -*- coding: utf-8 -*-
"""Analysis plugin to gather information about Chrome extensions."""

import re

import requests

from plaso.analysis import interface
from plaso.analysis import logger
from plaso.analysis import manager
from plaso.containers import analysis_results


class ChromeExtensionPlugin(interface.AnalysisPlugin):
  """Analysis plugin to gather information about Chrome extensions."""

  NAME = 'chrome_extension'

  _SUPPORTED_EVENT_DATA_TYPES = frozenset([
      'fs:stat'])

  _TITLE_RE = re.compile(r'<title>([^<]+)</title>')
  _WEB_STORE_URL = 'https://chrome.google.com/webstore/detail/{xid}?hl=en-US'

  _REQUEST_TIMEOUT = 60

  def __init__(self):
    """Initializes an Chrome extension analysis plugin."""
    super(ChromeExtensionPlugin, self).__init__()

    # Saved list of already looked up extensions.
    self._extensions = {}
    self._extensions_per_user = {}

  def _GetChromeWebStorePage(self, extension_identifier):
    """Retrieves the page for the extension from the Chrome store website.

    Args:
      extension_identifier (str): Chrome extension identifier.

    Returns:
      str: page content or None.
    """
    web_store_url = self._WEB_STORE_URL.format(xid=extension_identifier)
    try:
      response = requests.get(web_store_url, timeout=self._REQUEST_TIMEOUT)

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
    if path[0] in ('\\', '/'):
      return path[0]

    if path[1:].startswith(':\\'):
      return '\\'

    backward_slash_count = path.count('\\')
    forward_slash_count = path.count('/')
    if backward_slash_count > forward_slash_count:
      return '\\'

    return '/'

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
      self._extensions[extension_identifier] = None
      return None

    self._extensions[extension_identifier] = name
    return name

  def CompileReport(self, analysis_mediator):
    """Compiles an analysis report.

    Args:
      analysis_mediator (AnalysisMediator): mediates interactions between
          analysis plugins and other components, such as storage and dfVFS.

    Returns:
      AnalysisReport: analysis report.
    """
    for username, extensions in sorted(self._extensions_per_user.items()):
      for extension, extension_identifier in sorted(extensions):
        analysis_result = analysis_results.ChromeExtensionAnalysisResult(
            extension=extension, extension_identifier=extension_identifier,
            username=username)
        analysis_mediator.ProduceAnalysisResult(analysis_result)

        self._analysis_counter[username] += 1

    return super(ChromeExtensionPlugin, self).CompileReport(analysis_mediator)

  # pylint: disable=unused-argument
  def ExamineEvent(
      self, analysis_mediator, event, event_data, event_data_stream):
    """Analyzes an event.

    Args:
      analysis_mediator (AnalysisMediator): mediates interactions between
          analysis plugins and other components, such as storage and dfVFS.
      event (EventObject): event to examine.
      event_data (EventData): event data.
      event_data_stream (EventDataStream): event data stream.
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

    username = analysis_mediator.GetUsernameForPath(filename)

    # We still want this information in here, so that we can
    # manually deduce the username.
    if not username:
      if len(filename) > 25:
        username = 'Not found ({0:s}...)'.format(filename[0:25])
      else:
        username = 'Not found ({0:s})'.format(filename)

    extension_string = self._GetTitleFromChromeWebStore(extension_identifier)
    if not extension_string:
      extension_string = extension_identifier

    self._extensions_per_user.setdefault(username, [])
    extension_tuple = (extension_string, extension_identifier)
    if extension_tuple not in self._extensions_per_user[username]:
      self._extensions_per_user[username].append(extension_tuple)


manager.AnalysisPluginManager.RegisterPlugin(ChromeExtensionPlugin)
