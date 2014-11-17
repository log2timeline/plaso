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
"""bencode_interface contains basic interface for bencode plugins within Plaso.

Bencoded files are only one example of a type of object that the Plaso tool is
expected to encounter and process.  There can be and are many other parsers
which are designed to process specific data types.

BencodePlugin defines the attributes necessary for registration, discovery
and operation of plugins for bencoded files which will be used by
BencodeParser.
"""

import abc
import logging

from plaso.lib import errors
from plaso.parsers import plugins


class BencodePlugin(plugins.BasePlugin):
  """This is an abstract class from which plugins should be based."""

  # BENCODE_KEYS is a list of keys required by a plugin.
  # This is expected to be overridden by the processing plugin.
  # Ex. frozenset(['activity-date', 'done-date'])
  BENCODE_KEYS = frozenset(['any'])

  # This is expected to be overridden by the processing plugin.
  # URLS should contain a list of URLs with additional information about
  # this key or value.
  # Ex. ['https://wiki.theory.org/BitTorrentSpecification#Bencoding']
  URLS = []

  NAME = 'bencode'

  def _GetKeys(self, data, keys, depth=1):
    """Helper function to return keys nested in a bencode dict.

    By default this function will return the values for the named keys requested
    by a plugin in match{}. The default setting is to look a single layer down
    from the root (same as the check for plugin applicability). This level is
    suitable for most cases.

    For cases where there is variability in the name at the first level
    (e.g. it is the MAC addresses of a device, or a UUID) it is possible to
    override the depth limit and use _GetKeys to fetch from a deeper level.

    Args:
      data: bencode data in dictionary form.
      keys: A list of keys that should be returned.
      depth: Defines how many levels deep to check for a match.

    Returns:
      A dictionary with just the keys requested.
    """
    keys = set(keys)
    match = {}

    if depth == 1:
      for key in keys:
        match[key] = data[key]
    else:
      for _, parsed_key, parsed_value in self._RecurseKey(
          data, depth=depth):
        if parsed_key in keys:
          match[parsed_key] = parsed_value
          if set(match.keys()) == keys:
            return match
    return match

  def _RecurseKey(self, recur_item, root='', depth=15):
    """Flattens nested dictionaries and lists by yielding it's values.

    The hierarchy of a bencode file is a series of nested dictionaries and
    lists. This is a helper function helps plugins navigate the structure
    without having to reimplement their own recursive methods.

    This method implements an overridable depth limit to prevent processing
    extremely deeply nested dictionaries. If the limit is reached a debug
    message is logged indicating which key processing stopped on.

    Args:
      recur_item: An object to be checked for additional nested items.
      root: The pathname of the current working key.
      depth: A counter to ensure we stop at the maximum recursion depth.

    Yields:
      A tuple of the root, key, and value from a bencoded file.
    """
    if depth < 1:
      logging.debug(u'Recursion limit hit for key: {0:s}'.format(root))
      return

    if type(recur_item) in (list, tuple):
      for recur in recur_item:
        for key in self._RecurseKey(recur, root, depth):
          yield key
      return

    if not hasattr(recur_item, 'iteritems'):
      return

    for key, value in recur_item.iteritems():
      yield root, key, value
      if isinstance(value, dict):
        value = [value]
      if isinstance(value, list):
        for item in value:
          if isinstance(item, dict):
            for keyval in self._RecurseKey(
                item, root=root + u'/' + key, depth=depth - 1):
              yield keyval

  @abc.abstractmethod
  def GetEntries(
      self, parser_context, file_entry=None, parser_chain=None, data=None,
      match=None, **kwargs):
    """Extracts event object from the values of entries within a bencoded file.

    This is the main method that a bencode plugin needs to implement.

    The contents of the bencode keys defined in BENCODE_KEYS can be made
    available to the plugin as both a matched{'KEY': 'value'} and as the
    entire bencoded data dictionary. The plugin should implement logic to parse
    the most relevant data set into a useful event for incorporation into the
    Plaso timeline.

    The attributes for a BencodeEvent should include the following:
      root = Root key this event was extracted from.
      key = Key the value resided in.
      time = Date this artifact was created in microseconds(usec) from epoch.
      desc = Short description.

    Args:
      parser_context: A parser context object (instance of ParserContext).
      file_entry: Optional file entry object (instance of dfvfs.FileEntry).
                  The default is None.
      parser_chain: Optional string containing the parsing chain up to this
                    point. The default is None.
      data: Bencode data in dictionary form. The default is None.
      match: Optional dictionary containing only the keys selected in the
             BENCODE_KEYS. The default is None.
    """

  def Process(
      self, parser_context, file_entry=None, parser_chain=None,
      data=None, **kwargs):
    """Determine if this is the correct plugin; if so proceed with processing.

    Process() checks if the current bencode file being processed is a match for
    a plugin by comparing the PATH and KEY requirements defined by a plugin. If
    both match processing continues; else raise WrongBencodePlugin.

    This function also extracts the required keys as defined in
    self.BENCODE_KEYS from the file and stores the result in match[key]
    and calls self.GetEntries() which holds the processing logic implemented by
    the plugin.

    Args:
      parser_context: A parser context object (instance of ParserContext).
      file_entry: Optional file entry object (instance of dfvfs.FileEntry).
                  The default is None.
      parser_chain: Optional string containing the parsing chain up to this
                    point. The default is None.
      data: Bencode data in dictionary form. The default is None.

    Raises:
      WrongBencodePlugin: If this plugin is not able to process the given file.
      ValueError: If top level is not set.
    """
    if data is None:
      raise ValueError(u'Data is not set.')

    if not set(data.keys()).issuperset(self.BENCODE_KEYS):
      raise errors.WrongBencodePlugin(self.NAME)

    # This will raise if unhandled keyword arguments are passed.
    super(BencodePlugin, self).Process(parser_context, **kwargs)

    logging.debug(u'Bencode Plugin Used: {0:s}'.format(self.NAME))
    match = self._GetKeys(data, self.BENCODE_KEYS, 3)

    # Add ourselves to the parser chain, which will be used in all subsequent
    # event creation in this parser.
    parser_chain = self._BuildParserChain(parser_chain)

    self.GetEntries(
        parser_context, file_entry=file_entry, data=data,
        parser_chain=parser_chain, match=match)
