#!/usr/bin/python
# -*- coding: utf-8 -*-
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
"""Extract search history from a plaso storage file and enjoy a cup of tea.

A very simple script that takes as an input a plaso storage file
and then tries to extract common search engine history from it and spit
it out to your lovely little screen or a file of your choosings.
"""
import argparse
import locale
import logging
import os
import sys
import urllib

# pylint: disable-msg=unused-import
from plaso import filters
from plaso import formatters

from plaso.lib import output
from plaso.lib import storage

# Here we define filters and callback methods for all hits on each filter.
FILTERS = (
    (('source is "WEBHIST" and url iregexp "(www.|encrypted.|/)google." and '
      'url contains "search"'), 'GoogleSearch'),
    ('source is "WEBHIST" and url contains "youtube.com"', 'YouTube'),
    (('source is "WEBHIST" and url contains "bing.com" and url contains '
      '"search"'), 'BingSearch'),
    ('source is "WEBHIST" and url contains "mail.google.com"', 'Gmail'),
    (('source is "WEBHIST" and url contains "yandex.com" and url contains '
      '"yandsearch"'), 'Yandex'),
    ('source is "WEBHIST" and url contains "duckduckgo.com"', 'DuckDuckGo')
)


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

  if not '%' in line:
    return line

  try:
    return unicode(urllib.unquote(str(line)), 'utf-8')
  except UnicodeDecodeError:
    logging.warning(u'Unable to decode line: %s', line)

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
    if 'search' not in string:
      return False

    if 'q=' not in string:
      return False

    return True

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


def Main():
  """Run the tool."""
  arg_parser = argparse.ArgumentParser(
      description=(
          'plaso_extract_search_history is a simple script that reads the '
          'content of a plaso storage file and tries to extract known search '
          'engine history from it'))

  arg_parser.add_argument(
      '-w', '--write', metavar='FILENAME', action='store', dest='output_file',
      default='', help='Write results to a file.')

  arg_parser.add_argument(
      'filename', action='store', metavar='STORAGE_FILE', help=(
          'The path to the plaso storage file.'))

  options = arg_parser.parse_args()
  preferred_encoding = locale.getpreferredencoding()
  if preferred_encoding.lower() == 'ascii':
    preferred_encoding = 'utf-8'

  if not os.path.isfile(options.filename):
    raise RuntimeError(u'File {} does not exist'.format(options.filename))

  results = {}
  result_count = {}

  output_filehandle = output.OutputFilehandle(preferred_encoding)
  if options.output_file:
    output_filehandle.Open(path=options.output_file)
  else:
    output_filehandle.Open(sys.stdout)

  # Build filters.
  filter_dict = {}
  for filter_str, call_back in FILTERS:
    filter_obj = filters.GetFilter(filter_str)
    call_back_obj = getattr(FilterClass, call_back, None)
    results[call_back] = []
    if filter_obj and call_back_obj:
      filter_dict[filter_obj] = (call_back, call_back_obj)

  with storage.PlasoStorage(options.filename, read_only=True) as store:
    event_object = store.GetSortedEntry()
    while event_object:
      for filter_obj, call_backs in filter_dict.items():
        call_back_name, call_back_object = call_backs
        if filter_obj.Match(event_object):
          url_attribute = getattr(event_object, 'url', None)
          if not url_attribute:
            continue
          ret_line = ScrubLine(call_back_object(url_attribute))
          if not ret_line:
            continue
          if ret_line in results[call_back_name]:
            result_count[u'{}:{}'.format(call_back_name, ret_line)] += 1
          else:
            results[call_back_name].append(ret_line)
            result_count[u'{}:{}'.format(call_back_name, ret_line)] = 1
      event_object = store.GetSortedEntry()

  for engine_name, result_list in results.items():
    results_with_count = []
    for result in result_list:
      results_with_count.append((
          result_count[u'{}:{}'.format(engine_name, result)], result))

    header = u' == ENGINE: %s ==\n' % engine_name
    output_filehandle.WriteLine(header)
    for count, result in sorted(results_with_count, reverse=True):
      line = u'{} {}\n'.format(count, result)
      output_filehandle.WriteLine(line)
    output_filehandle.WriteLine('\n')


if __name__ == '__main__':
  Main()
