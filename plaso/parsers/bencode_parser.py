#!/usr/bin/python
# -*- coding: utf-8 -*-
#
# Copyright 2013 The Plaso Project Authors.
# Please see the AUTHORS file for details on individual authors.
#
# Licensed under the Apache License, Version 2.0 (the 'License');
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
"""This file contains the Bencode Parser.

Plaso's engine calls BencodeParser when it encounters bencoded files to be
processed, typically seen for BitTorrent data.
"""

import logging
import re
import os

import bencode

from plaso.lib import errors
from plaso.parsers import interface
from plaso.parsers import manager


class BencodeParser(interface.BasePluginsParser):
  """Deserializes bencoded file; produces a dictionary containing bencoded data.

  The Plaso engine calls parsers by their Parse() method. This parser's
  Parse() has GetTopLevel() which deserializes bencoded files using the
  BitTorrent-bencode library and calls plugins (BencodePlugin) registered
  through the interface by their Process() to produce event objects.

  Plugins are how this parser understands the content inside a bencoded file,
  each plugin holds logic specific to a particular bencoded file. See the
  bencode_plugins / directory for examples of how bencode plugins are
  implemented.
  """

  # Regex match for a bencode dictionary followed by a field size.
  BENCODE_RE = re.compile('d[0-9]')

  NAME = 'bencode'
  DESCRIPTION = u'Parser for bencoded files.'

  _plugin_classes = {}

  def __init__(self):
    """Initializes a parser object."""
    super(BencodeParser, self).__init__()
    self._plugins = BencodeParser.GetPluginObjects()

  def GetTopLevel(self, file_object):
    """Returns deserialized content of a bencoded file as a dictionary object.

    Args:
      file_object: A file-like object.

    Returns:
      Dictionary object representing the contents of the bencoded file.
    """
    header = file_object.read(2)
    file_object.seek(0, os.SEEK_SET)

    if not self.BENCODE_RE.match(header):
      raise errors.UnableToParseFile(u'Not a valid Bencoded file.')

    try:
      top_level_object = bencode.bdecode(file_object.read())
    except (IOError, bencode.BTFailure) as exception:
      raise errors.UnableToParseFile(
          u'Unable to parse invalid Bencoded file with error: {0:s}'.format(
              exception))

    if not top_level_object:
      raise errors.UnableToParseFile(u'Not a valid Bencoded file.')

    return top_level_object

  def Parse(self, parser_context, file_entry):
    """Parse and extract values from a bencoded file.

    Args:
      parser_context: A parser context object (instance of ParserContext).
      file_entry: A file entry object (instance of dfvfs.FileEntry).
    """
    file_object = file_entry.GetFileObject()
    top_level_object = self.GetTopLevel(file_object)

    if not top_level_object:
      file_object.close()
      raise errors.UnableToParseFile(
          u'[{0:s}] unable to parse: {1:s}. Skipping.'.format(
              self.NAME, file_entry.name))

    for plugin_object in self._plugins:
      try:
        plugin_object.Process(parser_context, top_level=top_level_object)

      except errors.WrongBencodePlugin as exception:
        logging.debug(u'[{0:s}] wrong plugin: {1:s}'.format(
            self.NAME, exception))

    file_object.close()


manager.ParsersManager.RegisterParser(BencodeParser)
