#!/usr/bin/python
# -*- coding: utf-8 -*-
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

import bencode
import logging
import re

from plaso import bencode_parser  # pylint: disable=W0611
from plaso.lib import bencode_interface
from plaso.lib import errors
from plaso.lib import parser


class BencodeParser(parser.PlasoParser):
  """Deserializes bencoded file; yields dictionary containing bencoded data.

  The Plaso engine calls parsers by their Parse() method. This parser's
  Parse() has GetTopLevel() which deserializes bencoded files using the
  BitTorrent-bencode library and calls plugins (BencodePlugin) registered
  through the bencode_interface by their Process() to yield BencodeEvent
  objects back to the engine.

  Plugins are how this parser understands the content inside a bencoded file,
  each plugin holds logic specific to a particular bencoded file. See the
  bencode_parser/ directory for examples of how bencode plugins are
  implemented.
  """

  # Regex match for a bencode dictionary followed by a field size.
  BENCODE_RE = re.compile('d[0-9]')

  def __init__(self, pre_obj):
    super(BencodeParser, self).__init__(pre_obj)
    self._plugins = bencode_interface.GetBencodePlugins()

  def GetTopLevel(self, file_object):
    """Returns deserialized content of a bencoded file as a dictionary object.

    Args:
      file_object: This is a file-like object pointing to the bencoded file.

    Returns:
      Dictionary object representing the contents of the bencoded file.
    """
    header = file_object.read(2)
    file_object.seek(0)

    if not self.BENCODE_RE.match(header):
      raise errors.UnableToParseFile(u'Not a valid Bencoded file.')

    try:
      top_level_object = bencode.bdecode(file_object.read())
    except (IOError, bencode.BTFailure) as e:
      raise errors.UnableToParseFile(
          u'Not a valid Bencoded file, unable to parse. '
          u'Reason given: {}'.format(e))

    if not top_level_object:
      raise errors.UnableToParseFile(u'Not a valid Bencoded file.')

    return top_level_object


  def Parse(self, filehandle):
    """Parse and extract values from a bencoded file.

    Args:
      filehandle: This is a file like object.

    Yields:
    An event.BencodeEvent containing information extracted from a bencoded
    file.
    """
    top_level_object = self.GetTopLevel(filehandle)
    if not top_level_object:
      raise errors.UnableToParseFile(
          u'[BENCODE] couldn\'t parse: %s.  Skipping.' % filehandle.name)

    for plugin in self._plugins:
      try:
        for evt in plugin.Process(top_level_object):
          yield evt
      except errors.WrongBencodePlugin as e:
        logging.debug(u'[BENCODE] Wrong Plugin:{}'.format(e[0]))
