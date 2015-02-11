# -*- coding: utf-8 -*-
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
      data_object = bencode.bdecode(file_object.read())
    except (IOError, bencode.BTFailure) as exception:
      raise errors.UnableToParseFile(
          u'Unable to parse invalid Bencoded file with error: {0:s}'.format(
              exception))

    if not data_object:
      raise errors.UnableToParseFile(u'Not a valid Bencoded file.')

    return data_object

  def Parse(self, parser_mediator, **kwargs):
    """Parse and extract values from a bencoded file.

    Args:
      parser_mediator: A parser mediator object (instance of ParserMediator).
    """
    file_object = parser_mediator.GetFileObject()
    data_object = self.GetTopLevel(file_object)

    if not data_object:
      file_object.close()
      raise errors.UnableToParseFile(
          u'[{0:s}] unable to parse: {1:s}. Skipping.'.format(
              self.NAME, parser_mediator.GetDisplayName()))

    for plugin_object in self._plugins:
      try:
        plugin_object.UpdateChainAndProcess(parser_mediator, data=data_object)
      except errors.WrongBencodePlugin as exception:
        logging.debug(u'[{0:s}] wrong plugin: {1:s}'.format(
            self.NAME, exception))

    file_object.close()


manager.ParsersManager.RegisterParser(BencodeParser)
