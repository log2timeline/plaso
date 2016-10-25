# -*- coding: utf-8 -*-
"""A plugin that extracts browser history from events."""

import collections
import logging
import re
import urllib

from plaso.analysis import interface
from plaso.analysis import manager
from plaso.containers import reports
from plaso.formatters import manager as formatters_manager
from plaso.lib import py2to3


# Create a lightweight object that is used to store timeline based information
# about each search term.
SEARCH_OBJECT = collections.namedtuple(
    u'SEARCH_OBJECT', u'time source engine search_term')


class BrowserSearchPlugin(interface.AnalysisPlugin):
  """Analyze browser search entries from events."""

  NAME = u'browser_search'

  # Indicate that we do not want to run this plugin during regular extraction.
  ENABLE_IN_EXTRACTION = False

  _EVENT_TAG_COMMENT = u'Browser Search'
  _EVENT_TAG_LABELS = [u'browser_search']

  # TODO: use groups to build a single RE.

  # Here we define filters and callback methods for all hits on each filter.
  _URL_FILTERS = frozenset([
      (u'Bing', re.compile(u'bing.com/search'), u'_ExtractSearchQueryFromURL'),
      (u'DuckDuckGo', re.compile(r'duckduckgo\.com'),
       u'_ExtractDuckDuckGoSearchQuery'),
      (u'GMail', re.compile(r'mail\.google\.com'),
       u'_ExtractGMailSearchQuery'),
      (u'Google Docs', re.compile(r'docs.google.com'),
       u'_ExtractGoogleDocsSearchQuery'),
      (u'Google Drive', re.compile(r'drive\.google\.com/drive/search'),
       u'_ExtractGoogleSearchQuery'),
      (u'Google Search',
       re.compile(r'(www\.|encrypted\.|/)google\.[^/]*/search'),
       u'_ExtractGoogleSearchQuery'),
      (u'Google Sites', re.compile(r'sites.google.com/site'),
       u'_ExtractGoogleSearchQuery'),
      (u'Yandex', re.compile(r'yandex\.com/search'),
       u'_ExtractYandexSearchQuery'),
      (u'Youtube', re.compile(r'youtube\.com'),
       '_ExtractYouTubeSearchQuery'),
  ])

  def __init__(self):
    """Initializes an analysis plugin."""
    super(BrowserSearchPlugin, self).__init__()
    self._counter = collections.Counter()

    # Store a list of search terms in a timeline format.
    # The format is key = timestamp, value = (source, engine, search term).
    self._search_term_timeline = []

  def _DecodeURL(self, url):
    """Decodes the URL, replaces %XX to their corresponding characters.

    Args:
      url (str): encoded URL.

    Returns:
      str: decoded URL.
    """
    if not url:
      return u''

    decoded_url = urllib.unquote(url)
    if isinstance(decoded_url, py2to3.BYTES_TYPE):
      try:
        decoded_url = decoded_url.decode(u'utf-8')
      except UnicodeDecodeError as exception:
        decoded_url = decoded_url.decode(u'utf-8', errors=u'replace')
        logging.warning(
            u'Unable to decode URL: {0:s} with error: {1:s}'.format(
                url, exception))

    return decoded_url

  def _ExtractDuckDuckGoSearchQuery(self, url):
    """Extracts a search query from a DuckDuckGo search URL.

    DuckDuckGo: https://duckduckgo.com/?q=query

    Args:
      url (str): URL.

    Returns:
      str: search query.
    """
    if u'q=' not in url:
      return

    return self._GetBetweenQEqualsAndAmbersand(url).replace(u'+', u' ')

  def _ExtractGMailSearchQuery(self, url):
    """Extracts a search query from a GMail search URL.

    GMail: https://mail.google.com/mail/u/0/#search/query[/?]

    Args:
      url (str): URL.

    Returns:
      str: search query.
    """
    if u'search/' not in url:
      return

    _, _, line = url.partition(u'search/')
    line, _, _ = line.partition(u'/')
    line, _, _ = line.partition(u'?')

    return line.replace(u'+', u' ')

  def _ExtractGoogleDocsSearchQuery(self, url):
    """Extracts a search query from a Google docs URL.

    Google Docs: https://docs.google.com/.*/u/0/?q=query

    Args:
      url (str): URL.

    Returns:
      str: search query.
    """
    if u'q=' not in url:
      return

    line = self._GetBetweenQEqualsAndAmbersand(url)
    if not line:
      return

    return line.replace(u'+', u' ')

  def _ExtractGoogleSearchQuery(self, url):
    """Extracts a search query from a Google URL.

    Google Drive: https://drive.google.com/drive/search?q=query
    Google Search: https://www.google.com/search?q=query
    Google Sites: https://sites.google.com/site/.*/system/app/pages/
                  search?q=query

    Args:
      url (str): URL.

    Returns:
      str: search query.
    """
    if u'search' not in url or u'q=' not in url:
      return

    line = self._GetBetweenQEqualsAndAmbersand(url)
    if not line:
      return

    return line.replace(u'+', u' ')

  def _ExtractYandexSearchQuery(self, url):
    """Extracts a search query from a Yandex search URL.

    Yandex: https://www.yandex.com/search/?text=query

    Args:
      url (str): URL.

    Returns:
      str: search query.
    """
    if u'text=' not in url:
      return
    _, _, line = url.partition(u'text=')
    before_and, _, _ = line.partition(u'&')
    if not before_and:
      return
    yandex_search_url = before_and.split()[0]

    return yandex_search_url.replace(u'+', u' ')

  def _ExtractYouTubeSearchQuery(self, url):
    """Extracts a search query from a YouTube search URL.

    YouTube: https://www.youtube.com/results?search_query=query

    Args:
      url (str): URL.

    Returns:
      str: search query.
    """
    return self._ExtractSearchQueryFromURL(url)

  def _ExtractSearchQueryFromURL(self, url):
    """Extracts a search query from the URL.

    Bing: https://www.bing.com/search?q=query
    GitHub: https://github.com/search?q=query

    Args:
      url (str): URL.

    Returns:
      str: search query, the value between 'q=' and '&'.
    """
    if u'search' not in url or u'q=' not in url:
      return

    return self._GetBetweenQEqualsAndAmbersand(url).replace(u'+', u' ')

  def _GetBetweenQEqualsAndAmbersand(self, url):
    """Retrieves the substring between the substrings 'q=' and '&'.

    Args:
      url (str): URL.

    Returns:
      str: search query, the value between 'q=' and '&'.
    """
    # Make sure we're analyzing the query part of the URL.
    _, _, url = url.partition(u'?')
    # Look for a key value pair named 'q'.
    _, _, url = url.partition(u'q=')
    if not url:
      return u''

    # Strip additional key value pairs.
    url, _, _ = url.partition(u'&')
    return url

  def CompileReport(self, mediator):
    """Compiles an analysis report.

    Args:
      mediator (AnalysisMediator): mediates interactions between
          analysis plugins and other components, such as storage and dfvfs.

    Returns:
      AnalysisReport: analysis report.
    """
    results = {}
    for key, count in iter(self._counter.items()):
      search_engine, _, search_term = key.partition(u':')
      results.setdefault(search_engine, {})
      results[search_engine][search_term] = count

    lines_of_text = []
    for search_engine, terms in sorted(results.items()):
      lines_of_text.append(u' == ENGINE: {0:s} =='.format(search_engine))

      for search_term, count in sorted(
          terms.items(), key=lambda x: (x[1], x[0]), reverse=True):
        lines_of_text.append(u'{0:d} {1:s}'.format(count, search_term))

      # An empty string is added to have SetText create an empty line.
      lines_of_text.append(u'')

    lines_of_text.append(u'')
    report_text = u'\n'.join(lines_of_text)
    analysis_report = reports.AnalysisReport(
        plugin_name=self.NAME, text=report_text)
    analysis_report.report_array = self._search_term_timeline
    analysis_report.report_dict = results
    return analysis_report

  def ExamineEvent(self, mediator, event):
    """Analyzes an event.

    Args:
      mediator (AnalysisMediator): mediates interactions between
          analysis plugins and other components, such as storage and dfvfs.
      event (EventObject): event to examine.
    """
    # This event requires an URL attribute.
    url = getattr(event, u'url', None)
    if not url:
      return

    # TODO: refactor this the source should be used in formatting only.
    # Check if we are dealing with a web history event.
    source, _ = formatters_manager.FormattersManager.GetSourceStrings(event)

    if source != u'WEBHIST':
      return

    for engine, url_expression, method_name in self._URL_FILTERS:
      callback_method = getattr(self, method_name, None)
      if not callback_method:
        logging.warning(u'Missing method: {0:s}'.format(callback_method))
        continue

      match = url_expression.search(url)
      if not match:
        continue

      search_query = callback_method(url)
      if not search_query:
        logging.warning(u'Missing search query for URL: {0:s}'.format(url))
        continue

      search_query = self._DecodeURL(search_query)
      if not search_query:
        continue

      event_tag = self._CreateEventTag(
          event, self._EVENT_TAG_COMMENT, self._EVENT_TAG_LABELS)
      mediator.ProduceEventTag(event_tag)

      self._counter[u'{0:s}:{1:s}'.format(engine, search_query)] += 1

      # Add the timeline format for each search term.
      timestamp = getattr(event, u'timestamp', 0)
      source = getattr(event, u'parser', u'N/A')
      source = getattr(event, u'plugin', source)
      self._search_term_timeline.append(
          SEARCH_OBJECT(timestamp, source, engine, search_query))


manager.AnalysisPluginManager.RegisterPlugin(BrowserSearchPlugin)
