# -*- coding: utf-8 -*-
"""A plugin that extracts browser history from events."""

import collections
import logging
import urllib

from plaso.analysis import interface
from plaso.analysis import manager
from plaso.filters import manager as filters_manager
from plaso.formatters import manager as formatters_manager
from plaso.lib import event


# Create a lightweight object that is used to store timeline based information
# about each search term.
SEARCH_OBJECT = collections.namedtuple(
    u'SEARCH_OBJECT', u'time source engine search_term')


class FilterClass(object):
  """A class that contains all the parser functions."""

  @classmethod
  def _ExtractSearchQueryFromURL(cls, url):
    """Extracts the search query from the URL.

    Args:
      url: Unicode string containing the URL.

    Returns:
      The search query substring, between the substrings 'q=' and '&'.
    """
    if not cls._SearchAndQInLine(url):
      return

    return cls._GetBetweenQEqualsAndAmbersand(url).replace(u'+', u' ')

  @classmethod
  def _GetBetweenQEqualsAndAmbersand(cls, string):
    """Determines the substring between the substrings 'q=' and '&'.

    Returns:
      A boolean value indicating a match.
    """
    if u'q=' not in string:
      return string
    _, _, line = string.partition(u'q=')
    before_and, _, _ = line.partition(u'&')
    if not before_and:
      return line
    return before_and.split()[0]

  @classmethod
  def _SearchAndQInLine(cls, string):
    """Determines if the susbstring 'q=' and 'search' appear in string.

    Returns:
      A boolean value indicating a match.
    """
    return u'search' in string and u'q=' in string

  @classmethod
  def BingSearch(cls, url):
    """Extracts the search query from the URL for Bing search.

    Args:
      url: Unicode string containing the URL.

    Returns:
      The search query substring.
    """
    return cls._ExtractSearchQueryFromURL(url)

  @classmethod
  def DuckDuckGo(cls, url):
    """Extracts the search query from the URL for DuckDuckGo search.

    Args:
      url: Unicode string containing the URL.

    Returns:
      The search query substring.
    """
    if not u'q=' in url:
      return

    return cls._GetBetweenQEqualsAndAmbersand(url).replace(u'+', u' ')

  @classmethod
  def Gmail(cls, url):
    """Extracts the search query from the URL for Gmail search.

    Args:
      url: Unicode string containing the URL.

    Returns:
      The search query substring.
    """
    if u'search/' not in url:
      return

    _, _, line = url.partition(u'search/')
    first, _, _ = line.partition(u'/')
    second, _, _ = first.partition(u'?compose')

    return second.replace(u'+', u' ')

  @classmethod
  def GoogleSearch(cls, url):
    """Extracts the search query from the URL for Google search.

    Args:
      url: Unicode string containing the URL.

    Returns:
      The search query substring.
    """
    if not cls._SearchAndQInLine(url):
      return

    line = cls._GetBetweenQEqualsAndAmbersand(url)
    if not line:
      return

    return line.replace(u'+', u' ')

  @classmethod
  def Yandex(cls, url):
    """Extracts the search query from the URL for Yandex search.

    Args:
      url: Unicode string containing the URL.

    Returns:
      The search query substring.
    """
    if u'text=' not in url:
      return
    _, _, line = url.partition(u'text=')
    before_and, _, _ = line.partition(u'&')
    if not before_and:
      return
    yandex_search_url = before_and.split()[0]

    return yandex_search_url.replace(u'+', u' ')

  @classmethod
  def YouTube(cls, url):
    """Extracts the search query from the URL for Youtube search.

    Args:
      url: Unicode string containing the URL.

    Returns:
      The search query substring.
    """
    return cls._ExtractSearchQueryFromURL(url)


class BrowserSearchPlugin(interface.AnalysisPlugin):
  """Analyze browser search entries from events."""

  NAME = u'browser_search'

  # Indicate that we do not want to run this plugin during regular extraction.
  ENABLE_IN_EXTRACTION = False

  # Here we define filters and callback methods for all hits on each filter.
  FILTERS = (
      ((u'url iregexp "(www.|encrypted.|/)google." and url contains "search"'),
       u'GoogleSearch'),
      (u'url contains "youtube.com"', u'YouTube'),
      ((u'source is "WEBHIST" and url contains "bing.com" and url contains '
        u'"search"'), u'BingSearch'),
      (u'url contains "mail.google.com"', u'Gmail'),
      ((u'source is "WEBHIST" and url contains "yandex.com" and url contains '
        u'"yandsearch"'), u'Yandex'),
      (u'url contains "duckduckgo.com"', u'DuckDuckGo')
  )

  def __init__(self, incoming_queue):
    """Initializes the browser search analysis plugin.

    Args:
      incoming_queue: A queue that is used to listen to incoming events.
    """
    super(BrowserSearchPlugin, self).__init__(incoming_queue)
    self._filter_dict = {}
    self._counter = collections.Counter()

    # Store a list of search terms in a timeline format.
    # The format is key = timestamp, value = (source, engine, search term).
    self._search_term_timeline = []

    for filter_str, call_back in self.FILTERS:
      filter_obj = filters_manager.FiltersManager.GetFilterObject(filter_str)
      call_back_obj = getattr(FilterClass, call_back, None)
      if filter_obj and call_back_obj:
        self._filter_dict[filter_obj] = (call_back, call_back_obj)

  def _ScrubLine(self, line):
    """Scrub the line of most obvious HTML codes.

    An attempt at taking a line and swapping all instances
    of %XX which represent a character in hex with it's
    unicode character.

    Args:
      line: The string that we are about to "fix".

    Returns:
      A Unicode string that has it's %XX hex codes swapped for text.
    """
    if not line:
      return u''

    try:
      # TODO: this is likely going to break on Python 3, fix this.
      return unicode(urllib.unquote(str(line)), u'utf-8')
    except UnicodeDecodeError:
      logging.warning(u'Unable to decode line: {0:s}'.format(line))

    return line

  def CompileReport(self, analysis_mediator):
    """Compiles a report of the analysis.

    Args:
      analysis_mediator: The analysis mediator object (instance of
                         AnalysisMediator).

    Returns:
      The analysis report (instance of AnalysisReport).
    """
    report = event.AnalysisReport(self.NAME)

    results = {}
    for key, count in self._counter.iteritems():
      search_engine, _, search_term = key.partition(u':')
      results.setdefault(search_engine, {})
      results[search_engine][search_term] = count
    report.report_dict = results
    report.report_array = self._search_term_timeline

    lines_of_text = []
    for search_engine, terms in sorted(results.items()):
      lines_of_text.append(u' == ENGINE: {0:s} =='.format(search_engine))

      for search_term, count in sorted(
          terms.iteritems(), key=lambda x: (x[1], x[0]), reverse=True):
        lines_of_text.append(u'{0:d} {1:s}'.format(count, search_term))

      # An empty string is added to have SetText create an empty line.
      lines_of_text.append(u'')

    report.SetText(lines_of_text)

    return report

  def ExamineEvent(
      self, unused_analysis_mediator, event_object, **unused_kwargs):
    """Analyzes an event object.

    Args:
      analysis_mediator: The analysis mediator object (instance of
                         AnalysisMediator).
      event_object: An event object (instance of EventObject).
    """
    # This event requires an URL attribute.
    url_attribute = getattr(event_object, u'url', None)

    if not url_attribute:
      return

    # TODO: refactor this the source should be used in formatting only.
    # Check if we are dealing with a web history event.
    source, _ = formatters_manager.FormattersManager.GetSourceStrings(
        event_object)

    if source != u'WEBHIST':
      return

    for filter_obj, call_backs in self._filter_dict.items():
      call_back_name, call_back_object = call_backs
      if filter_obj.Match(event_object):
        returned_line = self._ScrubLine(call_back_object(url_attribute))
        if not returned_line:
          continue
        self._counter[u'{0:s}:{1:s}'.format(call_back_name, returned_line)] += 1

        # Add the timeline format for each search term.
        timestamp = getattr(event_object, u'timestamp', 0)
        source = getattr(event_object, u'parser', u'N/A')
        source = getattr(event_object, u'plugin', source)
        self._search_term_timeline.append(SEARCH_OBJECT(
            timestamp, source, call_back_name, returned_line))


manager.AnalysisPluginManager.RegisterPlugin(BrowserSearchPlugin)
