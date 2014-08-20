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
# Register all bencode plugins.
from plaso.parsers import bencode_plugins  # pylint: disable=unused-import
from plaso.parsers import interface
from plaso.parsers import manager
from plaso.parsers.bencode_plugins import interface as bencode_plugins_interface


class BencodeParser(interface.BaseParser):
  """Deserializes bencoded file; yields dictionary containing bencoded data.

  The Plaso engine calls parsers by their Parse() method. This parser's
  Parse() has GetTopLevel() which deserializes bencoded files using the
  BitTorrent-bencode library and calls plugins (BencodePlugin) registered
  through the interface by their Process() to yield BencodeEvent
  objects back to the engine.

  Plugins are how this parser understands the content inside a bencoded file,
  each plugin holds logic specific to a particular bencoded file. See the
  bencode_plugins / directory for examples of how bencode plugins are
  implemented.
  """

  # Regex match for a bencode dictionary followed by a field size.
  BENCODE_RE = re.compile('d[0-9]')

  NAME = 'bencode'

  def __init__(self, pre_obj):
    """Initializes the parser.

    Args:
      pre_obj: pre-parsing object.
    """
    super(BencodeParser, self).__init__(pre_obj)
    self._plugins = manager.ParsersManager.GetRegisteredPlugins(
        parent_class=bencode_plugins_interface.BencodePlugin,
        pre_obj=self._pre_obj)

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

  def Parse(self, file_entry):
    """Parse and extract values from a bencoded file.

    Args:
      file_entry: A file entry object.

    Yields:
      An event.BencodeEvent containing information extracted from a bencoded
      file.
    """
    file_object = file_entry.GetFileObject()
    top_level_object = self.GetTopLevel(file_object)

    if not top_level_object:
      file_object.close()
      raise errors.UnableToParseFile(
          u'[{0:s}] unable to parse: {1:s}. Skipping.'.format(
              self.NAME, file_entry.name))

    for bencode_plugin in self._plugins.itervalues():
      try:
        for event_object in bencode_plugin.Process(top_level_object):
          event_object.plugin = bencode_plugin.plugin_name
          yield event_object

      except errors.WrongBencodePlugin as exception:
        logging.debug(u'[{0:s}] wrong plugin: {1:s}'.format(
            self.NAME, exception))

    file_object.close()
