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


class BencodeParser(interface.SingleFileBaseParser):
  """Deserializes bencoded file; produces a dictionary containing bencoded data.

  The Plaso engine calls parsers by their Parse() method. The Parse() function
  deserializes bencoded files using the BitTorrent-bencode library and
  calls plugins (BencodePlugin) registered through the interface by their
  Process() to produce event objects.

  Plugins are how this parser understands the content inside a bencoded file,
  each plugin holds logic specific to a particular bencoded file. See the
  bencode_plugins / directory for examples of how bencode plugins are
  implemented.
  """

  _INITIAL_FILE_OFFSET = None

  # Regex match for a bencode dictionary followed by a field size.
  BENCODE_RE = re.compile(r'd[0-9]')

  NAME = u'bencode'
  DESCRIPTION = u'Parser for bencoded files.'

  _plugin_classes = {}

  def __init__(self):
    """Initializes a parser object."""
    super(BencodeParser, self).__init__()
    self._plugins = BencodeParser.GetPluginObjects()

  def ParseFileObject(self, parser_mediator, file_object, **kwargs):
    """Parses a bencoded file-like object.

    Args:
      parser_mediator: A parser mediator object (instance of ParserMediator).
      file_object: A file-like object.

    Raises:
      UnableToParseFile: when the file cannot be parsed.
    """
    file_object.seek(0, os.SEEK_SET)
    header = file_object.read(2)
    if not self.BENCODE_RE.match(header):
      raise errors.UnableToParseFile(u'Not a valid Bencoded file.')

    file_object.seek(0, os.SEEK_SET)
    try:
      data_object = bencode.bdecode(file_object.read())

    except (IOError, bencode.BTFailure) as exception:
      raise errors.UnableToParseFile(
          u'[{0:s}] unable to parse file: {1:s} with error: {2:s}'.format(
              self.NAME, parser_mediator.GetDisplayName(), exception))

    if not data_object:
      raise errors.UnableToParseFile(
          u'[{0:s}] missing decoded data for file: {1:s}'.format(
              self.NAME, parser_mediator.GetDisplayName()))

    for plugin_object in self._plugins:
      try:
        plugin_object.UpdateChainAndProcess(parser_mediator, data=data_object)
      except errors.WrongBencodePlugin as exception:
        logging.debug(u'[{0:s}] wrong plugin: {1:s}'.format(
            self.NAME, exception))


manager.ParsersManager.RegisterParser(BencodeParser)
