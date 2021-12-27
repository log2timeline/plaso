# -*- coding: utf-8 -*-
"""A plugin that extracts browser history from events."""

import re

from urllib import parse as urlparse

from plaso.analysis import interface
from plaso.analysis import logger
from plaso.analysis import manager
from plaso.containers import analysis_results


class BrowserSearchPlugin(interface.AnalysisPlugin):
  """Analyze browser search entries from events."""

  NAME = 'browser_search'

  _EVENT_TAG_LABELS = ['browser_search']

  _SUPPORTED_EVENT_DATA_TYPES = frozenset([
      'chrome:autofill:entry',
      'chrome:cache:entry',
      'chrome:cookie:entry',
      'chrome:extension_activity:activity_log',
      'chrome:history:file_downloaded',
      'chrome:history:page_visited',
      'cookie:google:analytics:utma',
      'cookie:google:analytics:utmb',
      'cookie:google:analytics:utmt',
      'cookie:google:analytics:utmz',
      'firefox:cache:record',
      'firefox:cookie:entry',
      'firefox:downloads:download',
      'firefox:places:bookmark',
      'firefox:places:bookmark_annotation',
      'firefox:places:bookmark_folder',
      'firefox:places:page_visited',
      'msiecf:leak',
      'msiecf:redirected',
      'msiecf:url',
      'msie:webcache:container',
      'msie:webcache:containers',
      'msie:webcache:leak_file',
      'msie:webcache:partitions',
      'opera:history:entry',
      'opera:history:typed_entry',
      'safari:cookie:entry',
      'safari:history:visit',
      'safari:history:visit_sqlite'])

  # TODO: use groups to build a single RE.

  # Here we define filters and callback methods for all hits on each filter.
  _URL_FILTERS = frozenset([
      ('Bing', re.compile(r'bing\.com/search'), '_ExtractSearchQueryFromURL'),
      ('DuckDuckGo', re.compile(r'duckduckgo\.com'),
       '_ExtractDuckDuckGoSearchQuery'),
      ('GMail', re.compile(r'mail\.google\.com'),
       '_ExtractGMailSearchQuery'),
      ('Google Docs', re.compile(r'docs\.google\.com'),
       '_ExtractGoogleDocsSearchQuery'),
      ('Google Drive', re.compile(r'drive\.google\.com/drive/search'),
       '_ExtractGoogleSearchQuery'),
      ('Google Search',
       re.compile(r'(www\.|encrypted\.|/)google\.[^/]*/search'),
       '_ExtractGoogleSearchQuery'),
      ('Google Sites', re.compile(r'sites\.google\.com/site'),
       '_ExtractGoogleSearchQuery'),
      ('Yahoo', re.compile(r'yahoo\.com/search'),
       '_ExtractYahooSearchQuery'),
      ('Yandex', re.compile(r'yandex\.com/search'),
       '_ExtractYandexSearchQuery'),
      ('Youtube', re.compile(r'youtube\.com'),
       '_ExtractYouTubeSearchQuery'),
  ])

  def _ExtractDuckDuckGoSearchQuery(self, url):
    """Extracts a search query from a DuckDuckGo search URL.

    DuckDuckGo: https://duckduckgo.com/?q=query

    Args:
      url (str): URL.

    Returns:
      str: search query or None if no query was found.
    """
    if 'q=' not in url:
      return None

    return self._GetBetweenQEqualsAndAmpersand(url).replace('+', ' ')

  def _ExtractGMailSearchQuery(self, url):
    """Extracts a search query from a GMail search URL.

    GMail: https://mail.google.com/mail/u/0/#search/query[/?]

    Args:
      url (str): URL.

    Returns:
      str: search query or None if no query was found.
    """
    if 'search/' not in url:
      return None

    _, _, line = url.partition('search/')
    line, _, _ = line.partition('/')
    line, _, _ = line.partition('?')

    return line.replace('+', ' ')

  def _ExtractGoogleDocsSearchQuery(self, url):
    """Extracts a search query from a Google docs URL.

    Google Docs: https://docs.google.com/.*/u/0/?q=query

    Args:
      url (str): URL.

    Returns:
      str: search query  or None if no query was found.
    """
    if 'q=' not in url:
      return None

    line = self._GetBetweenQEqualsAndAmpersand(url)
    if not line:
      return None

    return line.replace('+', ' ')

  def _ExtractGoogleSearchQuery(self, url):
    """Extracts a search query from a Google URL.

    Google Drive: https://drive.google.com/drive/search?q=query
    Google Search: https://www.google.com/search?q=query
    Google Sites: https://sites.google.com/site/.*/system/app/pages/
                  search?q=query

    Args:
      url (str): URL.

    Returns:
      str: search query or None if no query was found.
    """
    if 'search' not in url or 'q=' not in url:
      return None

    line = self._GetBetweenQEqualsAndAmpersand(url)
    if not line:
      return None

    return line.replace('+', ' ')

  def _ExtractYahooSearchQuery(self, url):
    """Extracts a search query from a Yahoo search URL.

    Examples:
      https://search.yahoo.com/search?p=query
      https://search.yahoo.com/search;?p=query

    Args:
      url (str): URL.

    Returns:
      str: search query or None if no query was found.
    """
    if 'p=' not in url:
      return None
    _, _, line = url.partition('p=')
    before_and, _, _ = line.partition('&')
    if not before_and:
      return None
    yahoo_search_url = before_and.split()[0]

    return yahoo_search_url.replace('+', ' ')

  def _ExtractYandexSearchQuery(self, url):
    """Extracts a search query from a Yandex search URL.

    Yandex: https://www.yandex.com/search/?text=query

    Args:
      url (str): URL.

    Returns:
      str: search query or None if no query was found.
    """
    if 'text=' not in url:
      return None
    _, _, line = url.partition('text=')
    before_and, _, _ = line.partition('&')
    if not before_and:
      return None
    yandex_search_url = before_and.split()[0]

    return yandex_search_url.replace('+', ' ')

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
      str: search query, the value between 'q=' and '&' or None if no
          query was found.
    """
    if 'search' not in url or 'q=' not in url:
      return None

    return self._GetBetweenQEqualsAndAmpersand(url).replace('+', ' ')

  def _GetBetweenQEqualsAndAmpersand(self, url):
    """Retrieves the substring between the substrings 'q=' and '&'.

    Args:
      url (str): URL.

    Returns:
      str: search query, the value between 'q=' and '&'  or None if no query
      was found.
    """
    # Make sure we're analyzing the query part of the URL.
    _, _, url = url.partition('?')
    # Look for a key value pair named 'q'.
    _, _, url = url.partition('q=')
    if not url:
      return ''

    # Strip additional key value pairs.
    url, _, _ = url.partition('&')
    return url

  def CompileReport(self, analysis_mediator):
    """Compiles an analysis report.

    Args:
      analysis_mediator (AnalysisMediator): mediates interactions between
          analysis plugins and other components, such as storage and dfVFS.

    Returns:
      AnalysisReport: analysis report.
    """
    for lookup_key, number_of_queries in self._analysis_counter.items():
      search_engine, _, search_term = lookup_key.partition(':')

      analysis_result = analysis_results.BrowserSearchAnalysisResult(
          number_of_queries=number_of_queries, search_engine=search_engine,
          search_term=search_term)
      analysis_mediator.ProduceAnalysisResult(analysis_result)

    return super(BrowserSearchPlugin, self).CompileReport(analysis_mediator)

  def ExamineEvent(
      self, analysis_mediator, event, event_data, event_data_stream):
    """Analyzes an event.

    Args:
      analysis_mediator (AnalysisMediator): mediates interactions between
          analysis plugins and other components, such as storage and dfVFS.
      event (EventObject): event.
      event_data (EventData): event data.
      event_data_stream (EventDataStream): event data stream.
    """
    if event_data.data_type not in self._SUPPORTED_EVENT_DATA_TYPES:
      return

    url = getattr(event_data, 'url', None)
    if not url:
      return

    for engine, url_expression, method_name in self._URL_FILTERS:
      callback_method = getattr(self, method_name, None)
      if not callback_method:
        logger.warning(
            'Missing callback method: {0:s} to parse search query'.format(
                method_name))
        continue

      match = url_expression.search(url)
      if not match:
        continue

      search_query = callback_method(url)
      if not search_query:
        analysis_mediator.ProduceAnalysisWarning(
            'Unable to determine search query: {0:s} in URL: {1:s}'.format(
                method_name, url), self.NAME)
        continue

      try:
        search_query = urlparse.unquote(search_query)
      except TypeError:
        search_query = None

      if not search_query:
        analysis_mediator.ProduceAnalysisWarning(
            'Unable to decode search query: {0:s} in URL: {1:s}'.format(
                method_name, url), self.NAME)
        continue

      event_tag = self._CreateEventTag(event, self._EVENT_TAG_LABELS)
      analysis_mediator.ProduceEventTag(event_tag)

      lookup_key = '{0:s}:{1:s}'.format(engine, search_query)
      self._analysis_counter[lookup_key] += 1


manager.AnalysisPluginManager.RegisterPlugin(BrowserSearchPlugin)
