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
"""A plugin that extracts browser history from events."""

import collections
import logging
import urllib

from plaso import filters
from plaso.analysis import interface
from plaso.lib import event
from plaso.lib import eventdata


def ScrubLine(line):
  """Scrub the line of most obvious HTML codes.

  An attempt at taking a line and swapping all instances
  of %XX which represent a character in hex with it's
  unicode character.

  Args:
    line: The string that we are about to "fix".

  Returns:
    String that has it's %XX hex codes swapped for text.
  """
  if not line:
    return ''

  try:
    return unicode(urllib.unquote(str(line)), 'utf-8')
  except UnicodeDecodeError:
    logging.warning(u'Unable to decode line: {0:s}'.format(line))

  return line


class FilterClass(object):
  """A class that contains all the parser functions."""

  @classmethod
  def _GetBetweenQEqualsAndAmbersand(cls, string):
    """Return back string that is defined 'q=' and '&'."""
    if 'q=' not in string:
      return string
    _, _, line = string.partition('q=')
    before_and, _, _ = line.partition('&')
    if not before_and:
      return line
    return before_and.split()[0]

  @classmethod
  def _SearchAndQInLine(cls, string):
    """Return a bool indicating if the words q= and search appear in string."""
    return 'search' in string and 'q=' in string

  @classmethod
  def GoogleSearch(cls, url):
    """Return back the extracted string."""
    if not cls._SearchAndQInLine(url):
      return

    line = cls._GetBetweenQEqualsAndAmbersand(url)
    if not line:
      return

    return line.replace('+', ' ')

  @classmethod
  def YouTube(cls, url):
    """Return back the extracted string."""
    return cls.GenericSearch(url)

  @classmethod
  def BingSearch(cls, url):
    """Return back the extracted string."""
    return cls.GenericSearch(url)

  @classmethod
  def GenericSearch(cls, url):
    """Return back the extracted string from a generic search engine."""
    if not cls._SearchAndQInLine(url):
      return

    return cls._GetBetweenQEqualsAndAmbersand(url).replace('+', ' ')

  @classmethod
  def Yandex(cls, url):
    """Return back the results from Yandex search engine."""
    if 'text=' not in url:
      return
    _, _, line = url.partition('text=')
    before_and, _, _ = line.partition('&')
    if not before_and:
      return
    yandex_search_url = before_and.split()[0]

    return yandex_search_url.replace('+', ' ')

  @classmethod
  def DuckDuckGo(cls, url):
    """Return back the extracted string."""
    if not 'q=' in url:
      return
    return cls._GetBetweenQEqualsAndAmbersand(url).replace('+', ' ')

  @classmethod
  def Gmail(cls, url):
    """Return back the extracted string."""
    if 'search/' not in url:
      return

    _, _, line = url.partition('search/')
    first, _, _ = line.partition('/')
    second, _, _ = first.partition('?compose')

    return second.replace('+', ' ')


class AnalyzeBrowserSearchPlugin(interface.AnalysisPlugin):
  """Analyze browser search entries from events."""

  NAME = 'browser_search'

  # Indicate that we do not want to run this plugin during regular extraction.
  ENABLE_IN_EXTRACTION = False

  # Here we define filters and callback methods for all hits on each filter.
  FILTERS = (
      (('url iregexp "(www.|encrypted.|/)google." and url contains "search"'),
       'GoogleSearch'),
      ('url contains "youtube.com"', 'YouTube'),
      (('source is "WEBHIST" and url contains "bing.com" and url contains '
        '"search"'), 'BingSearch'),
      ('url contains "mail.google.com"', 'Gmail'),
      (('source is "WEBHIST" and url contains "yandex.com" and url contains '
        '"yandsearch"'), 'Yandex'),
      ('url contains "duckduckgo.com"', 'DuckDuckGo')
  )

  def __init__(self, pre_obj, incoming_queue, outgoing_queue):
    """Constructor for the browser history plugin."""
    super(AnalyzeBrowserSearchPlugin, self).__init__(
        pre_obj, incoming_queue, outgoing_queue)
    self._filter_dict = {}
    self._counter = collections.Counter()

    for filter_str, call_back in self.FILTERS:
      filter_obj = filters.GetFilter(filter_str)
      call_back_obj = getattr(FilterClass, call_back, None)
      if filter_obj and call_back_obj:
        self._filter_dict[filter_obj] = (call_back, call_back_obj)

  def ExamineEvent(self, event_object):
    """Take an EventObject and send it through analysis."""
    # This event requires an URL attribute.
    url_attribute = getattr(event_object, 'url', None)

    if not url_attribute:
      return

    # Check if we are dealing with a web history event.
    source, _ = eventdata.EventFormatterManager.GetSourceStrings(event_object)

    if source != 'WEBHIST':
      return

    for filter_obj, call_backs in self._filter_dict.items():
      call_back_name, call_back_object = call_backs
      if filter_obj.Match(event_object):
        returned_line = ScrubLine(call_back_object(url_attribute))
        if not returned_line:
          continue
        self._counter[u'{}:{}'.format(call_back_name, returned_line)] += 1

  def CompileReport(self):
    """Compiles a report of the analysis.

    Returns:
      The analysis report (instance of AnalysisReport).
    """
    report = event.AnalysisReport()

    results = {}
    for key, count in self._counter.iteritems():
      search_engine, _, search_term = key.partition(':')
      results.setdefault(search_engine, {})
      results[search_engine][search_term] = count
    report.report_dict = results

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
